# Current backups for VMC are sitting on vSAN storage WITHIN VMC.
# This script runs as a scheduled task after backups complete and does two things
# 1) It sync's the backups from the local NFS to my S3 Bucket
# 2) It logs the sync to a text file.

# Get today's date and replace the '/' with '-' so that it can be used in a filename
$date = ((get-date).ToShortDateString()).Replace('/','-')

# Using AWSCLI installed on the machine, sync all files in the t:\backups to s3 and log it
aws s3 sync --region us-west-2 t:\backups s3://vmctmm-backups  > "c:\temp\$date.txt"

# Log is usually decently large. Search for the 'progress' lines and send everything else to -minimal
Get-Content c:\temp\$date.txt | Select-string -pattern "Completed" -notmatch | out-file c:\temp\$date-minimal.txt

# Delete the large log file
Remove-Item -Path c:\temp\$date.txt -Confirm:$false

