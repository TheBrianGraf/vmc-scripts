<# This script will allow you to automatically disconnect or route NSX-T Segments in VMC.
 If you want this to be fully automated, you can add values to all variables below, otherwise
 the script will prompt you for the orgname and sddc name.
 I can take time later to add prompts for refresh token, segment name, and action. this was
 just to get this out quickly.
#>

# Not required to set, but automates if you do
$orgname = 'Demo Lab'
$sddcName = 'Demo-Lab-SDDC'

# Required variables 
$refreshtoken = 's@mp1er3fr3sht0k3n'
$segmentidentifier = "bgraf*" # Use '*' as a wildcard for segment names if needed
$segmentation = "ROUTED" # Choose 'ROUTED' to connect the segments and 'DISCONNECTED' to disconnect the segments


# Check for the VMC NSXT Module
if (get-module -listavailable | where-object {$_.name -eq 'VMware.VMC.NSXT'}) {
    Write-Host 'VMware.VMC.NSXT module exists. Continuing with script.' -ForegroundColor Yellow
    Continue
} else {
    # If not installed, try to get it  from the PowerShell gallery
    Write-Host 'VMware.VMC.NSXT module does not exist. Attempting to install the module to continue' -ForegroundColor Yellow
    Write-host 'Starting Install...' -ForegroundColor Green
    Install-Module 'VMware.VMC.NSXT' -Force
    try {
        $modexists = get-module -listavailable | where-object {$_.name -eq 'VMware.VMC.NSXT'}
    }
    Catch {
        Write-Host "An Error has occurred. Please try installing the VMware.VMC.NSXT module and restart the script"
    }
}



# Connect to VMC 
Connect-vmcserver -ApiToken $refreshtoken

# If the org name above is empty, query the org and select the correct one
if ($orgname -eq $null) {
    $orgs = Get-VmcOrganization
    if (($orgs).count -gt 1){
        write-host "___ ORGANIZATION SELECTION MENU ___"
        $menu = @{}
        for ($i=1; $i -le $orgs.count; $i++)
        {
            Write-Host "$i - $($orgs[$i-1].name)"
            $menu.Add($i, ($orgs[$i-1].name))
        }
        do {
            write-host "Select your org"
            [int]$ans = Read-Host 'Choose an Org'
        } until ($ans -ge 1 -and $ans -le $i)
        
        $orgname = $menu.Item($ans)
        $orgid = ($orgs | where {$_.name -eq $orgname}).id
        
    } else {
            $orgname = $orgs.name
            $orgid = $orgs.Id
    }
} else {
    # If it has been added above, use it.
    $orgid = (get-VmcOrganization -Name $orgname).id
}

# If the SDDC name is not added above, query SDDCs for user to choose
if ($sddcname -eq $null) {
    $SDDCs = Get-VmcSddc
    if (($SDDCs).count -gt 1){
        write-host "___ SDDC SELECTION MENU ___"
        $menu = @{}
        for ($i=1; $i -le $SDDCs.count; $i++)
        {
            Write-Host "$i - $($SDDCs[$i-1].name)"
            $menu.Add($i, ($SDDCs[$i-1].name))
        }
        do {
            write-host "Select your SDDC"
            [int]$ans = Read-Host 'Choose an SDDC'
        } until ($ans -ge 1 -and $ans -le $i)
        
        $sddcname = $menu.Item($ans)
        $sddcid = ($sddcs | where {$_.name -eq $sddcname}).id
        write-host "SDDC: $sddcname ID: $sddcid"
    } else {
            $sddcname = $SDDCs.name
            $sddcid = $SDDCs.Id
            write-host "SDDC: $sddcname ID: $sddcid"
    }
} else {
    # Otherwise use the selected SDDC
    $sddcid = (get-vmcsddc -name $sddcname).id
}
write-host $orgid
write-host $sddcid
#### 

# Connect to the NSX-T Proxy with this information
Connect-NSXTProxy -RefreshToken $refreshtoken -OrgName $orgname -SDDCName $sddcName

# Return all NSX Segments like the variable added above
if ($segmentidentifier -ne $null){
    $segments = Get-NSXTSegment | where {$_.Name -like "$segmentidentifier"} 
    $segments
}
if ($segmentation -ne $null) {
    switch ($segmentation) { 
        "DISCONNECTED" { 
            $segments = Get-NSXTSegment | where {$_.Name -like "$segmentidentifier" -and $_.TYPE -eq "ROUTED"} 
        }
        "ROUTED" {
            $segments = Get-NSXTSegment | where {$_.Name -like "$segmentidentifier" -and $_.TYPE -eq "DISCONNECTED"} 
        }
    }
}
foreach ($segment in $segments){

    switch ($segmentation){
        "DISCONNECTED" { 
            Set-NSXTSegment -Name $segment.Name -Disconnected 
        }
        "ROUTED" {
            Set-NSXTSegment -Name $segment.Name -Connected
        }
    }
    
}


