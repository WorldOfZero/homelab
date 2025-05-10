# Copy this to $PROFILE
Import-Module posh-git
Import-Module -Name Terminal-Icons # Adds icons to terminal results
Import-Module PSReadLine

# Setup Oh My Posh
oh-my-posh init pwsh --config 'https://raw.githubusercontent.com/JanDeDobbeleer/oh-my-posh/refs/heads/main/themes/night-owl.omp.json' | Invoke-Expression

# TODO: Create seperate Aliases file

# Powershell ReadLine helpers
Set-PSReadLineOption -BellStyle Visual
Set-PSReadLineKeyHandler -Key Tab -Function Complete