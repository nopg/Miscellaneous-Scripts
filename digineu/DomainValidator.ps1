####
#
# Author: Jared Whiting
# Description: Digicert -> Neustar Domain Validator
# Date: 3/2022
# 
#
####
Class DomainValidator {
    [System.Boolean]$enableDebug;
    [hashtable]$headers;
    [System.String]$APIKeyFile;
    DomainValidator() {
        $this.enableDebug = $true;
        $this.APIKeyFile = "APIKey.txt"
        $a = Get-Content $this.APIKeyFile
        $this.headers = @{
            'X-DC-DEVKEY'="$a"
        };
        $this.Run();
    }
    [void] Debug([string]$msg, [int]$level) {
        if ($this.enableDebug) {
            $callingFunction = $(Get-PSCallStack)[1].FunctionName
            $callingClass = $(Get-PSCallStack)[2].FunctionName
            $msg = "[$callingClass]::$callingFunction says $msg";
            $this._Debug($msg,$level)
        }
    }
    [void] Debug([string]$msg, [Exception]$e) {
        if ($this.enableDebug) {
            $callingFunction = $(Get-PSCallStack)[1].FunctionName
            $callingClass = $(Get-PSCallStack)[2].FunctionName
            $eType = @($_.Exception.GetType() | select -ExpandProperty Name -First 1)
            $eMsg = $_.Exception.Message
            $msg = "[$callingClass]::$callingFunction says Exception -> $eType -> $eMsg -> $msg";
            $this._Debug($msg,4);
        }
        Get-Date
    }
    [void] _Debug([string]$msg, [int]$level) {
        $colors = @{4 = "RED"; 3 = "YELLOW"; 2 = "BLUE"; 1 = "GREEN"; 0 = "WHITE"};
        $now = Get-Date
        $msg = "$now : $msg"
        Write-Host -foreground $colors.$level $msg;
    }


    [int] GetExpiryDomainCount() {
        try {
            $responseJSON = Invoke-WebRequest -Method 'GET' -Header $this.headers -Uri 'https://www.digicert.com/services/v2/domain/expiration-count' 
            $releases = ConvertFrom-Json $responseJSON.content
            return $releases.number_of_expiry_soon_domains
        } catch {
            $this.Debug("Something went wrong...", $_.Exception)
        }
        return -1;
    }

    [void] GetExpiryDomains() {
        try {
            $expDate = (Get-Date).adddays(180);
            $responseJSON = Invoke-WebRequest -Method 'GET' -Header $this.headers -Uri 'https://www.digicert.com/services/v2/domain'#?limit=1000' 
            $response = ConvertFrom-Json $responseJSON.content;
            foreach($d in $response.domains){
                foreach($e in $D.dcv_expiration){
                    $ev = [Datetime]::ParseExact($e.ev, 'yyyy-MM-dd', $null)
                    $ov = [Datetime]::ParseExact($e.ov, 'yyyy-MM-dd', $null)
                    $mindate = ($ev -lt $ov) ? $ev : $ov;
                    $ts = New-TimeSpan -Start (Get-Date) -End $mindate
                    if ($mindate -lt $expDate) {
                        $this.Debug($d.name + " id:" + $d.id + " expires in " + $ts.Days + " days. DCV validation is " + $d.dcv_method,1)
                    }
                }
            }
        } catch {
            $this.Debug("Something went wrong...", $_.Exception)
        }
    }


    [void] Run() {
        $edc = $this.GetExpiryDomainCount();
        $this.GetExpiryDomains();
        if ($edc -gt 0){
            $this.Debug("$edc expiry domains found.",1)
            $this.GetExpiryDomains();
        } else {
            $this.Debug("No expiry domains found.",0)
        }
    }
}
$o = [DomainValidator]::new();

