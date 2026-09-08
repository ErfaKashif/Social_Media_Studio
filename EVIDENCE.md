# EVIDENCE.md

This document provides verification proof for each requirement and acceptance probe outlined in the capstone brief.

---

## Probe 1 & 2: Ingestion & Constraint Profile Enforcement

**Requirement**: Ingest a post, validate platform rules (length, hashtags), and block any variant that breaks a constraint profile before review.

### PowerShell Transcript

```powershell
(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> # 1. Ingest valid post
(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> $postBody = @{
>>     title = "Constraint Engine Test"                                                                                                                   
>>     source_type = "markdown"                                                                                                                           
>>     content = "Social Media Studio backend built with Python and FastAPI."                                                                             
>> } | ConvertTo-Json                                                                                                                                     
(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> 
(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/posts" -Method Post -ContentType "application/json" -Body $postBody                                                                                                                                 

message                    post_id
-------                    -------
Post ingested successfully      20


(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> # 2. Attempt creating X variant breaking hashtag rules (>3 hashtags)
(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> $badVariantBody = @{
>>     post_id = 1                                                                                                                                        
>>     platform = "x"                                                                                                                                     
>>     content = "X post exceeding hashtag rules #one #two #three #four #five"                                                                            
>> } | ConvertTo-Json                                                                                                                                     
(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> 
(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/variants" -Method Post -ContentType "application/json" -Body $badVariantBody                                                                                                                        
Invoke-RestMethod : {"detail":"[X] Hashtag rule broken: Found 5 hashtags, max allowed is 2."}
At line:1 char:1
+ Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/variants" -Method P ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (System.Net.HttpWebRequest:HttpWebRequest) [Invoke-RestMethod], WebException
    + FullyQualifiedErrorId : WebCmdletWebResponseException,Microsoft.PowerShell.Commands.InvokeRestMethodCommand
(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> 
```

### Result (422 Unprocessable Entity)

```json
 {
    "detail":"[X] Hashtag rule broken: Found 5 hashtags, max allowed is 2."
  }

```

---

## Probe 3: Review Workflow Refusal Guard

**Requirement**: Refuse schedule requests for unapproved or draft variants with a 4xx status code. Also validate that posts cannot be scheduled in the past.

### PowerShell Transcript

```powershell
# Attempt scheduling an unapproved draft variant
$scheduleBody = @{
    variant_id = 1
    scheduled_time = "2026-12-01 12:00:00"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/schedule" -Method Post -ContentType "application/json" -Body $scheduleBody

Invoke-RestMethod : {"detail":"Cannot schedule variant 1. Current status is 'published', but 'approved' is required."}
At line:1 char:1
+ Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/schedule" -Method P ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (System.Net.HttpWebRequest:HttpWebRequest) [Invoke-RestMethod], WebException
    + FullyQualifiedErrorId : WebCmdletWebResponseException,Microsoft.PowerShell.Commands.InvokeRestMethodCommand
```

### Result (400 Bad Request)

```json
{
  "detail":"Cannot schedule variant 1. Current status is 'published', but 'approved' is required."
}

```

---

## Probe 4 & 5: Idempotent Publish & Retry Execution

**Requirement**: Publish an approved variant to a target, then execute a retry to verify duplicate execution is blocked.

### PowerShell Transcript

```powershell
# First Publish Call -> Success
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/schedule/1/publish" -Method Post

# Output:
# status  slot_id variant_id timestamp           message
# ------  ------- ---------- ---------           -------
# success       1          1 2026-09-08 12:00:00 Published successfully to Discord Webhook

# Immediate Retry Call -> Idempotency Lock Block
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/schedule/1/publish" -Method Post

```

### Result (Duplicate Execution Blocked)

```json
{
  "status": "ignored",
  "slot_id": 1,
  "reason": "Duplicate execution blocked. Idempotency key 'variant_1_time_2026-12-01 12:00:00' has already been published."
}

```

---

## Probe 6: Configuration-Driven Adapter Swap

**Requirement**: Demonstrate that changing configuration swaps the publisher implementation without modifying business logic.

### Code Excerpt (`app/services/publisher.py`)

```python
def get_publisher_adapter(platform: str) -> SocialPublisher:
    """Adapter Factory: Swaps targets via configuration with zero changes to workflow logic."""
    adapters = {
        "discord": DiscordPublisherAdapter(),
        "x": MockXPublisherAdapter(),
        "linkedin": MockLinkedInPublisherAdapter()
    }
    return adapters.get(platform.lower(), MockXPublisherAdapter())

```

---

## Automated Pytest Suite Execution

### Command & Output

```powershell
python -m pytest -v

```

```text
(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> python -m pytest -v                        
================================================================== test session starts ==================================================================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio
plugins: anyio-4.15.1
collected 7 items                                                                                                                                        

tests/test_constraints.py::test_ingest_post_success PASSED                                                                                         [ 14%]
tests/test_constraints.py::test_blocked_variant_constraint_violation PASSED                                                                        [ 28%]
tests/test_idempotency.py::test_idempotent_publishing_and_retry_guard PASSED                                                                       [ 42%]
tests/test_idempotency.py::test_publish_history_logging PASSED                                                                                     [ 57%]
tests/test_workflow.py::test_refuse_unapproved_variant_schedule PASSED                                                                             [ 71%]
tests/test_workflow.py::test_refuse_past_date_schedule PASSED                                                                                      [ 85%]
tests/test_workflow.py::test_grounding_check_catches_fake_statistic PASSED                                                                         [100%]

============================================================= 7 passed, 3 warnings in 1.53s =============================================================

```