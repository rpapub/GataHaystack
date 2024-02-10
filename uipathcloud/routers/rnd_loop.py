from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from ..config import Settings, get_settings
from ..models.uipathcloud import *
import httpx
from pydantic import parse_obj_as
from uuid import UUID

router = APIRouter(
    prefix="/uipathcloud",
    tags=["libraries (alpha)", "uipathcloud"],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


@router.get("/loop", tags=["debug"])
async def read_loop(request: Request, settings: Settings = Depends(get_settings)):
    accept_header = request.headers.get("accept", "")
    access_token = settings.uipathcloud_organizations[0].applications[0].access_tokens[0].access_token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "*/*",
        "User-Agent": "httpx",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        for i, organization in enumerate(settings.uipathcloud_organizations):
            # Fetch organization and tenant info
            org_url = f"{settings.uipathcloud_baseurl}/{organization.name}/portal_/api/filtering/leftnav/tenantsAndOrganizationInfo"
            org_response = await client.get(org_url, headers=headers)
            if org_response.status_code == 200:
                response_data = org_response.json()
                tenant_data = response_data.get('tenants', [])
                
                for j, tenant_dict in enumerate(tenant_data):
                    # Fetch and update Machines for each Tenant
                    machines_url = f"{settings.uipathcloud_baseurl}/{organization.name}/{tenant_dict['name']}/orchestrator_/odata/Machines"
                    print("---------machines_url: " + machines_url)
                    machine_response = await client.get(machines_url, headers=headers)
                    print("---------machine_response.status_code: " + str(machine_response.status_code))
                    if machine_response.status_code == 200:
                        machines_data = machine_response.json().get('value', [])
                        tenant_data[j]['machines'] = parse_obj_as(List[Machine], machines_data)

                    # Fetch and update Folders for each Tenant
                    folders_url = f"{settings.uipathcloud_baseurl}/{organization.name}/{tenant_dict['name']}/orchestrator_/odata/Folders"
                    print("---------folders_url: " + folders_url)
                    folders_response = await client.get(folders_url, headers=headers)
                    print("---------folders_response.status_code: " + str(folders_response.status_code))
                    if folders_response.status_code == 200:
                        folders_data = folders_response.json().get('value', [])
                        for k, folder_dict in enumerate(folders_data):
                            processes_url = f"{settings.uipathcloud_baseurl}/{organization.name}/{tenant_dict['name']}/orchestrator_/odata/Processes"
                            print("---------processes_url: " + processes_url)
                            process_headers = headers.copy()
                            process_headers["X-UIPATH-OrganizationUnitId"] = str(folder_dict['Id'])
                            processes_response = await client.get(processes_url, headers=process_headers)
                            print("---------processes_response.status_code: " + str(processes_response.status_code))
                            if processes_response.status_code == 200:
                                processes_data = processes_response.json().get('value', [])
                                folders_data[k]['processes'] = parse_obj_as(List[Process], processes_data)
                        
                        #tenant.folders = parse_obj_as(List[Folder], folders_data)
                        tenant_data[j]['folders'] = parse_obj_as(List[Folder], folders_data)

                    # Fetch and update Packages for each Tenant
                    packages_url = f"{settings.uipathcloud_baseurl}/{organization.name}/{tenant_dict['name']}/orchestrator_/odata/Releases"
                    print("---------packages_url: " + packages_url)
                    packages_response = await client.get(packages_url, headers=headers)
                    print("---------packages_response.status_code: " + str(packages_response.status_code))
                    if packages_response.status_code == 200:
                        packages_data = packages_response.json().get('value', [])
                        #tenant.packages = parse_obj_as(List[Package], packages_data)
                        tenant_data[j]['packages'] = parse_obj_as(List[Package], packages_data)

                    # Fetch and update Libraries for each Tenant
                    libraries_url = f"{settings.uipathcloud_baseurl}/{organization.name}/{tenant_dict['name']}/orchestrator_/odata/Libraries"
                    print("---------libraries_url: " + libraries_url)
                    libraries_response = await client.get(libraries_url, headers=headers)
                    print("---------libraries_response.status_code: " + str(libraries_response.status_code))
                    if libraries_response.status_code == 200:
                        libraries_data = libraries_response.json().get('value', [])
                        #tenant.libraries = parse_obj_as(List[Library], libraries_data)
                        tenant_data[j]['libraries'] = parse_obj_as(List[Library], libraries_data)
                      
                # Re-parse the updated tenants into the organization
                updated_tenants = parse_obj_as(List[Tenant], tenant_data)
                
                # Update the organization in settings
                updated_org_data = organization.dict(exclude={'tenants'})
                updated_org_data['tenants'] = updated_tenants
                settings.uipathcloud_organizations[i] = Organization.parse_obj(updated_org_data)

            else:
                print(f"Failed to fetch or update data for organization {organization.name}")


    #print(settings)
    data = {"libraries": "dummy"}
    if "application/json" in accept_header:
        return data
    else:
        return templates.TemplateResponse("test.html", {"request": request, "data": data, "settings": settings.mask_sensitive_data()})

