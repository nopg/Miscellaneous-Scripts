New-AzResourceGroup -Name <resource-group-name> -Location <resource-group-location> #use this command when you need to create a new resource group for your deployment
New-AzResourceGroupDeployment -ResourceGroupName <resource-group-name> -TemplateUri https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/101-vm-simple-linux/azuredeploy.json

az ps:
#create a new resource group for your deployment
az group create --name <resource-group-name> --location <resource-group-location> 
#deploy
az deployment group create --resource-group <my-resource-group> --template-uri https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/101-vm-simple-linux/azuredeploy.json

#list Regions:
az account list-locations

#Retrieve weird error details
az monitor activity-log list --correlation-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx





#AZURE SCHEMA JSON
https://github.com/Azure/azure-resource-manager-schemas