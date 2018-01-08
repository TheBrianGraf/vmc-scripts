<#
    .NOTES
    ===========================================================================
	 Created by:   	Brian Graf
     Date:          January 8, 2018
	 Organization: 	VMware
     Blog:          brianjgraf.com
     Twitter:       @vBrianGraf
	===========================================================================

	.DESCRIPTION
    This will allow you to deploy an RDS Database while concurrently deploying 3 Virtual Machines in the VMware Stack. It assumes your security group
    is already configured to allow communication between VMC and AWS

	.NOTES
    Requires AWSPowerShell Module be installed and configured
    Requires PowerCLI Modules to be installed
    Requires 'write-ProgressEx' module to be installed (https://www.powershellgallery.com/packages/write-ProgressEx/0.17)
#>

Write-host " ______        _                                          
(_____ \      | |                        _                
 _____) )_____| |____ _   _ _____ ____ _| |_              
|  __  /| ___ | |  _ \ | | | ___ |  _ (_   _)             
| |  \ \| ____| | | | \ V /| ____| | | || |_              
|_|   |_|_____)_|_| |_|\_/ |_____)_| |_| \__)             
                                                          
 _                                          _             
| |       _                             _  (_)            
| |____ _| |_ _____  ____  ____ _____ _| |_ _  ___  ____  
| |  _ (_   _) ___ |/ _  |/ ___|____ (_   _) |/ _ \|  _ \ 
| | | | || |_| ____( (_| | |   / ___ | | |_| | |_| | | | |
|_|_| |_| \__)_____)\___ |_|   \_____|  \__)_|\___/|_| |_|
                   (_____|           " -ForegroundColor Yellow

# ----- Edit Variables below -----

# AWS Variables
$DBName = "hybridenvironment"
$DBInstanceIdentifier = "hybridenvironment"
$SecurityGroupID = "sg-1ddab475" # Replace with your own security Group ID
$SubnetGroupName = "default-vpc-fac36d8c" # Replace with your Subnet group name
$allocatedStorageGB = '5'
$AvailabilityZone = 'us-west-2a'
$InstanceClass = 'db.m1.small'
$MasterUsername = 'vmcadmin'
$MasterPass = 'VMware1!'
$Engine = 'mysql'

# VMware Variables
$vCenter = ""
$vCUser = ""
$vCPass = ""

$ResourcePool = "BG-RP"
$Datastore = "WorkloadDatastore"
$Folder = "Workloads"
$WinTemplate = "TMPL-Win2012r2"
$UbuntuTemplate = "TMPL-Ubuntu"
$PhotonTemplate = "TMPL-Photon"
# ----- End Variable Editing -----

# Create the RDS Instance
Write-host "Creating RDS Database in us-west-2a" -ForegroundColor yellow 
$newDB = New-RDSDBInstance `
    -AllocatedStorage $allocatedStorageGB `
    -AvailabilityZone $AvailabilityZone `
    -DBInstanceClass $InstanceClass `
    -DBInstanceIdentifier $DBInstanceIdentifier `
    -DBName $DBName `
    -MasterUsername $MasterUsername `
    -MasterUserPassword $MasterPass `
    -PubliclyAccessible $false `
    -engine $Engine `
    -VpcSecurityGroupId $SecurityGroupID `
    -DBSubnetGroupName $SubnetGroupName

    Write-host "RDS Database Provisioning Started" -ForegroundColor yellow 
    $newdb | select DBName, DBInstanceClass, AvailabilityZone, PubliclyAccessible,Engine,VPCSecurityGroups,allocate

    # Connect to Cloud SDDC
Write-host "Connecting to Cloud vCenter Server" -ForegroundColor yellow 
Connect-VIServer -Server $vCenter -Protocol https -User $vCUser -Password $vCPass
Write-host "Connected!" -ForegroundColor Green


# Specify VMware Environmental Variables
$RP = Get-ResourcePool $ResourcePool
$DS = Get-Datastore $Datastore
$WorkFolder = Get-Folder $Folder
$WindowsTemplate = Get-Template $WinTemplate
$LinuxTemplate = Get-Template $UbuntuTemplate
$PhotonOSTemplate = Get-Template $PhotonTemplate

# Deploy Windows, Ubuntu, and Photon VMs

# Get Current VMs
$CurrentVMs = Get-VM -Location $RP

Write-Host "Checking for Existing VMs. If they exist, we'll increase the final integer
" -ForegroundColor yellow 
# If a deployment already exists, find the latest one
if ($CurrentVMs -like "Hybrid_Windows*") {
$HybridVMs = Get-VM "Hybrid_Windows*" | Sort-Object -Descending
if ($HybridVMs[0].Name.Substring($HybridVMs[0].Name.length - 1) -match '^[0-9]+$') {

    # Return the last digit of the newest deployment
    [int]$NextNum = $HybridVMs[0].Name.Substring($HybridVMs[0].Name.length - 1)
} else {
    [int]$NextNum = 0
}

# Increase the digit by one
$NextNum ++
}

# Create an Array of the VMs being deployed
Write-host "VMs will be deployed with ($NextNum) integer
" -ForegroundColor yellow 
$DeployedVMs = @()

# Deploy Windows VM
Write-host "Deploying (Hybrid_Windows$NextNum) VM " -ForegroundColor yellow 
$NewWinVM = New-VM -Name "Hybrid_Windows$NextNum" -Template $WindowsTemplate -Datastore $DS -ResourcePool $RP -Location $WorkFolder -DiskStorageFormat thin -RunAsync
$DeployedVMs += "Hybrid_Windows$NextNum"

# Deploy Ubuntu VM
Write-host "Deploying (Hybrid_Ubuntu$NextNum) VM " -ForegroundColor yellow 
$NewLinuxVM = New-VM -Name "Hybrid_Ubuntu$NextNum" -Template $LinuxTemplate -Datastore $DS -ResourcePool $RP -Location $WorkFolder -DiskStorageFormat thin -RunAsync
$DeployedVMs += "Hybrid_Windows$NextNum"

# Deploy Photon VM
Write-Host "Deploying (Hybrid_Photon$NextNum) VM " -ForegroundColor yellow 
$NewPhotonVM = New-VM -Name "Hybrid_Photon$NextNum" -Template $PhotonOSTemplate -Datastore $DS -ResourcePool $RP -Location $WorkFolder -DiskStorageFormat thin -RunAsync
$DeployedVMs += "Hybrid_Windows$NextNum"


    ###write-host "Checking Database Status"
    
    $RDSStatus = Get-RDSDBInstance $DBInstanceIdentifier
       
        # Don't worry about this. it's just messy
        $Wincount = 1
        $UbuntuCount = 1
        $photonCount = 1
        $WinStage = 0
        $UbuntuStage = 0
        $PhotonStage = 0

        # Do this until all 3 VMs have been deployed
        Do {

            # Return the vCenter Tasks
            $task = Get-Task

            # Variables for finding each of the Tasks related to each VM deploy
            $WinTask = $Task | where {$_.ID -eq $NewWinVM.Id}
            $UbuntuTask = $Task | where {$_.ID -eq $NewLinuxVM.Id}
            $PhotonTask = $Task | where {$_.ID -eq $NewPhotonVM.Id}

            # Progress bars for checking the VMs [THIS PART IS STILL A WORK IN PROGRESS]
            Write-ProgressEx -Activity "Deploying VMware VMs" -NoProgressBar -Id 1

            if ($Wintask.state -ne "Success"){
                write-ProgressEx -Total 100 -id 5 -Status "Deploying (Hybrid_Windows$NextNum) From Template" -Activity "Deploying Windows VM" -PercentComplete $Wincount -ParentId 1 -Increment
                $Wincount ++
             } else {
                 write-ProgressEx "Windows" -Total 100 -id 5 -Status "Deployed" -Completed -ParentId 1
                 $WinStage = 1
            }
             if ($UbuntuTask.state -ne "Success"){
                write-ProgressEx "Ubuntu" -Total 100 -id 2 -Status "Deploying" -ParentId 1
                $UbuntuCount ++
             } else {
                write-ProgressEx "Ubuntu" -Total 100 -id 2 -Status "Deployed" -Completed -ParentId 1
                $UbuntuStage = 1
           }
            if ($PhotonTask.state -ne "Success") {
                write-ProgressEx "Photon" -Total 100 -id 3 -Status "Deploying" -ParentId 1 -NoProgressBar
                $PhotonCount ++
            } else {
                write-ProgressEx "Photon" -Total 100 -id 3 -Status "Deployed" -Completed -ParentId 1
                $PhotonStage = 1
           }
            Start-sleep -seconds 5
            
            # Once all three VMs have deployed, move on.
        } until ($WinStage -eq 1 -and $UbuntuStage -eq 1 -and $PhotonStage -eq 1)
        
        Write-Host "All 3 VMs have deployed successfully" -ForegroundColor Green
        write-ProgressEx -Total 100 -id 5 -Status "Deploying (Hybrid_Windows$NextNum) From Template" -Activity "Deploying Windows VM" -PercentComplete $Wincount -ParentId 1 -Completed

        # Check the Database provisioning status
        Write-Host "Checking Database Status" -NoNewline

        # Keep checking every 10 seconds until DB is no longer being created.
        Do {$RDSStatus = Get-RDSDBInstance $DBInstanceIdentifier
            write-host "." -NoNewline
            start-sleep -Seconds 10} until ($RDSStatus.DBInstanceStatus -ne "Creating")
        Write-host "
        Database Created, Moving to Backup
        " -ForegroundColor Green
    
    # Check until the DB is no longer being backed up.

    do {$RDSStatus = Get-RDSDBInstance $DBInstanceIdentifier
        write-host "." -NoNewline
        start-sleep -Seconds 10} until ($RDSStatus.DBInstanceStatus -ne "backing-up")
        Write-host "
Database Backup complete. VMs and Database ready to use!" -ForegroundColor Green

        
        
