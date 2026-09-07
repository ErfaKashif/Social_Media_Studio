PROBE 3. Test Unapproved Scheduling Safeguard (MUST FAIL with 400 Error)
(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> $schedBody = @{
>>     variant_id = $variant.variant_id                                                                                                                   
>>     scheduled_time = "2026-09-08 12:00:00"                                                                                                             
>> } | ConvertTo-Json                                                                                                                                     
(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> 
(.venv) PS C:\Users\LAPTOP\PycharmProjects\socialmeda_Studio> Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/schedule" -Method Post -ContentType "application/json" -Body $schedBody                                                                                                                             
Invoke-RestMethod : {"detail":"Cannot schedule variant 1. Current status is 'draft', but 'approved' is required."}
At line:1 char:1
+ Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/schedule" -Method P ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (System.Net.HttpWebRequest:HttpWebRequest) [Invoke-RestMethod], WebException
    + FullyQualifiedErrorId : WebCmdletWebResponseException,Microsoft.PowerShell.Commands.InvokeRestMethodCommand
