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
    This will allow you to vMotion workloads from VMware Cloud on AWS to your on-premises environment

	.NOTES
    PLEASE NOTE THAT THIS REQUIRES L2 Stretch Network between your on-prem environment and VMC. Without the Layer2 VPN, vMotion will not work.
#>

# VMC 2 On-Prem
# ------------- VARIABLES SECTION - EDIT THE VARIABLES BELOW ------------- 
$destinationvCenter = "vcsa-tmm-02.onprem.lab" 
$destinationvCenterUser = "admin@onprem.lab"
$destinationvCenterPassword = "VMware1!"
$DestinationCluster = "Cluster-1"
$DestinationPortGroup = "Stretch-Network"
$DestinationDatastore = "CPBU_*"
$DestinationFolder = "VM"

$SourcevCenter = "vcenter.sddc-52-35-58-16.vmc.vmware.com"
$SourcevCenterUser = "cloudadmin@vmc.local"
$SourcevCenterPassword = 'VMware1!'

# This is an easy way to select which VMs will vMotion down to your on-prem environment.
$VMs = "*Linux*"

# ------------- END VARIABLES - DO NOT EDIT BELOW THIS LINE ------------- 
$destVCConn = connect-viserver $destinationvCenter -User $destinationvCenterUser -Password $destinationvCenterPassword
$sourceVCConn = Connect-VIServer -Server $SourcevCenter -Protocol https -User $SourcevCenterUser -Password $SourcevCenterPassword

$i = 1
$CountVMstoMove = (Get-VM $VMs -Server $sourceVCConn).Count
foreach ($VM in (get-VM $VMs -Server $sourceVCConn)) {
    $networkAdapter = Get-NetworkAdapter -VM $vm -Server $sourceVCConn
    $destination = Get-Cluster $DestinationCluster -server $destVCConn | get-resourcepool -server $destVCConn
    $destinationPortGroup = Get-VDPortgroup -Name $DestinationPortGroup -Server $destVCConn
    $destinationDatastore = Get-Datastore $DestinationDatastore -Server $destVCConn
    $folder = get-folder $DestinationFolder -server $destVCConn

    Write-host "($i of $CountVMsToMove) Moving " -NoNewline
    Write-host "$($VM.name) " -NoNewline -ForegroundColor Yellow
    Write-host "from " -NoNewline
    Write-host "($SourcevCenter) " -NoNewline -ForegroundColor Yellow
    Write-host "to " -NoNewline
    Write-host "($DestinationvCenter) " -ForegroundColor Yellow
    
    $Duration = Measure-Command {Move-VM -VM $vm -Destination $destination -NetworkAdapter $networkAdapter -inventorylocation $folder -PortGroup $destinationPortGroup -Datastore $destinationDatastore | Out-Null } | Out-Null
    
    Write-host "    ($i of $CountVMsToMove) Move of $($VM.name) Completed in ($Duration) Minutes!" -ForegroundColor Green
    
    $i++
}
##############################################