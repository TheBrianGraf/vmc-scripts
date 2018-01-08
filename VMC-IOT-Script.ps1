
# Requires AWSPowerShell Module. Either add logic to add it automatically or make sure it's installed
import-module AWSPowerShell

# Set Region to the region of your VMC SDDC
Set-DefaultAWSRegion -Region us-west-2

# I've already setup my AWS Credetials (named 'default')
Set-AWSCredentials -ProfileName default

# Import PowerCLI Module
import-module VMware.VimAutomation.Core

$vcenter = 'your vCenter Address'
$vcuser =  'your vCenter User'
$vcpass =  'your vCenter Password'

# Connect to vCenter
Write-host "Connecting to vCenter..." -ForegroundColor Yellow
$connection1 = Connect-VIServer -Server $vcenter -User $vcuser -Password $vcpass
if ($connection1) {Write-Host "Connected!" -ForegroundColor Green} 

# Creating a timeout on querying SQS Messages
# Run for ~ 1 week
$timeout = new-timespan -minutes 10000
$sw = [diagnostics.stopwatch]::StartNew()
$Button = $Null

# Create an array of the VMs auto-created so they can also be deleted
$VMArray = @()

Write-Host "Waiting on IoT Button Press:..." -ForegroundColor Yellow

# Do this until we hit the 1 week timeout
while ($sw.elapsed -lt $timeout) {

    # Query the SQS Queue for our IoT Messages
    $Button = Receive-SQSMessage -QueueUrl '' # Add the Queue you create in AWS here. example: "https://sqs.us-west-2.amazonaws.com/092437867744/test"
    
    # If there is something there, do this
    if ($Button -ne $Null){

        # Some code to make my life easier in reading the message
        $split = $button.body.split('"')
        $type = $split[-2]

        # Switch to determine what happens
        switch ($type) {

            # Long Press - Delete VM's created from short press
            "Long" {Write-host "Long Press" -ForegroundColor Green

            # Do something to each VM in the array
            Foreach ($VM in $VMArray) {
                
                # Remove the VM from the array as we are deleting it as well
                $VMArray = $VMarray -notlike "$vm"

                # Delete VM from vCenter
                Write-Host "Deleting VM: $VM from SDDC" -ForegroundColor Yellow
                Remove-VM $VM -DeletePermanently -RunAsync -Confirm:$false -ErrorAction SilentlyContinue
            }
    
                Write-Host "Long Press action completed" -ForegroundColor Green
                
            }
            # Regular Press - Create multiple VMs
            "Single" {
                Write-host "Short Press" -ForegroundColor Green

                # Just some variables..               
                if(
				    ($rp = Get-ResourcePool "Compute-ResourcePool" -server $connection1).count -gt 1
				) {
                    write-host "More than one RP"
                    $rp = Get-ResourcePool "Your Resource Pool Here" -server $connection1 | select-object -first 1  #ADD Your resource pool where you want the VMs to be deployed to
                    }
                $ds = get-datastore "WorkloadDatastore" -server $connection1
                $tmpl = get-template "Your Template Name Here" -server $connection1 # Change to a template you want to use
                $folder = Get-folder "Workloads" -server $connection1
               # Do the following 5 times
               1..5 | % {

               # Since it deploys relatively quickly, we use the time as part of the VM name.
               # Get the Date/Time to use in the VM Name
               $date = get-date
               $month = $date.Month
               $day = $date.Day
               $hour = $date.Hour
               $min = $date.minute
               $mil = $date.Millisecond

               # VMname is composition of Photon and the date/time
               $VMname = ("IOT-Photon-" + $month +$day + $hour + $min + $mil)

               # If two VMs try to provision during the same millisecond, it gives an error, 
               # so check if one already exists, if it does, add a random number between 0-10 to the end of the name
               if ($VMArray -eq $VMname) {$VMname = $VMName + (get-random -Maximum 10)}
               
               # Add VM Name to array
               $VMArray += $VMname

               # Create the new VM async
               New-VM -Name $VMname -ResourcePool $rp -location $folder -Datastore $ds -Template $tmpl -DiskStorageFormat thin  -server $connection1 -RunAsync }
               
               
               Write-Host "Short Press action completed" -ForegroundColor Green
            }

            # Double Press - Run Modified version of vCheck
            "Double" {
                Write-host "Double Press" -ForegroundColor Green
                Write-host "Running vCheck for VMware Cloud on AWS" -ForegroundColor Green

                # Run vCheck to analyze the environment. 
                # vCheck has been modified so that it will also push a copy of the report to S3
                # As well as make it public-read only, generate the link, and SMS it to my phone

                # vCheck for me is placed in c:\temp. you can change the directory below.
                . C:\temp\vCheck-vSphere-master\vCheck-vSphere-master\vCheck.ps1
                
                Write-Host "Double-Press action completed" -ForegroundColor Green
            }

        }

         # Time to remove the SQS Message from the queue so we can keep going.
         Remove-SQSMessage -QueueUrl "https://sqs.us-west-2.amazonaws.com/092437867744/test" -ReceiptHandle $button.receipthandle -Force
    }

  # Pause for 3 seconds and start querying again
  start-sleep -seconds 2
  }
