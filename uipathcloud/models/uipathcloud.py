from uuid import UUID
from pydantic import BaseModel, SecretStr, Field, validator, ValidationError, HttpUrl
from typing import List, Optional, Any, Dict
from datetime import datetime
from ..common import SecureDumpModel

VALID_GRANT_TYPES = ["authorization_code", "client_credentials", "refresh_token"]

class CurrentUser(BaseModel):
    Name: str
    Surname: str
    UserName: str
    Domain: Optional[str] = None
    DirectoryIdentifier: Optional[str] = None
    FullName: str
    EmailAddress: str
    IsEmailConfirmed: bool
    LastLoginTime: datetime
    IsActive: bool
    CreationTime: datetime
    AuthenticationSource: str
    Password: Optional[str] = None
    IsExternalLicensed: bool
    RolesList: List[str] = []
    LoginProviders: List[str]
    TenantId: int
    TenancyName: str
    TenantDisplayName: str
    TenantKey: UUID
    Type: str
    ProvisionType: str
    LicenseType: Optional[str] = None
    Key: UUID
    MayHaveUserSession: bool
    MayHaveRobotSession: bool
    MayHaveUnattendedSession: bool
    BypassBasicAuthRestriction: Optional[bool] = None
    MayHavePersonalWorkspace: bool
    RestrictToPersonalWorkspace: bool
    AccountId: UUID
    LastModificationTime: datetime
    LastModifierUserId: int
    CreatorUserId: Optional[int] = None
    Id: int
    PersonalWorskpaceFeedId: Optional[UUID] = None
    VirtualFolderId: int
    #RobotProvision: RobotProvision
    UnattendedRobot: Optional[str] = None  # Assuming string, adjust if needed
    #NotificationSubscription: NotificationSubscription
    UpdatePolicy: Optional[str] = None
    #Preferences: Preferences
    PersonalWorkspace: Optional[str] = None  # Assuming string, adjust if needed


class Tag(BaseModel):
    Name: str
    DisplayName: str
    Value: Optional[str] = None
    DisplayValue: Optional[str] = None

class ResourceTag(BaseModel):
    Name: str
    DisplayName: str
    Value: Optional[str] = None
    DisplayValue: Optional[str] = None

class AccessToken(BaseModel):
    grant_type: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires: Optional[int] = None
    token_type: str = "Bearer"

    @validator('grant_type')
    def check_grant_type_valid(cls, v): #pylint: disable=no-self-argument
        if v not in VALID_GRANT_TYPES:
            raise ValueError(f'Invalid grant type: {v}. Must be one of {VALID_GRANT_TYPES}')
        return v

class Application(BaseModel):
    app_name: str
    client_id: str
    client_secret: str
    scope: str
    grant_types: List[str] = Field(..., min_items=1, max_items=3)
    redirect_url: Optional[str] = None
    access_tokens: List[AccessToken] = []

class RobotVersion(BaseModel):
    Count: int
    Version: str

class RobotAccount(BaseModel):
    id: UUID
    name: str
    displayName: str
    creationTime: datetime
    lastLoginTime: Optional[datetime] = None
    groupIds: List[UUID]

class Group(BaseModel):
    id: UUID
    name: str
    displayName: str
    type: int
    creationTime: datetime = Field(alias='creationTime')
    lastModificationTime: Optional[datetime] = Field(alias='lastModificationTime', default=None)
    members: List[str] = []
    mappedRole: Optional[str] = None
    scope: Optional[str] = None

class MaintenanceWindow(BaseModel):
    Enabled: bool
    JobStopStrategy: str
    CronExpression: str
    TimezoneId: str
    Duration: int
    NextExecutionTime: Optional[datetime] = None

class Machine(BaseModel):
    LicenseKey: Optional[UUID] = None
    Name: str
    Description: Optional[str] = None
    Type: str
    Scope: str
    NonProductionSlots: int
    UnattendedSlots: int
    HeadlessSlots: int
    TestAutomationSlots: int
    AutomationCloudSlots: int
    AutomationCloudTestAutomationSlots: int
    Key: UUID
    EndpointDetectionStatus: str
    AutomationType: str
    TargetFramework: str
    ClientSecret: Optional[str] = None
    Id: int
    RobotVersions: List[RobotVersion] = Field(default_factory=list)
    RobotUsers: List[Any] = Field(default_factory=list)  # Assuming there's no detailed structure given
    UpdatePolicy: Optional[dict] = None  # This could be further detailed if the structure is known
    Tags: List[Tag] = Field(default_factory=list)
    #MaintenanceWindow: Optional[MaintenanceWindow] = None
    VpnSettings: Optional[Any] = None  # Assuming there's no detailed structure given

# # Assuming the JSON represents a list of machines directly
# class Machines(List[Machine]):
#     pass

class Library(BaseModel):
    Created: datetime
    LastUpdated: datetime
    Owners: Optional[str] = None
    IconUrl: Optional[str] = None
    Summary: Optional[str] = None
    PackageSize: int
    IsPrerelease: bool
    Title: Optional[str] = None
    Version: str
    Key: str
    Description: str
    Published: Optional[datetime] = None
    IsLatestVersion: bool
    OldVersion: Optional[str] = None
    ReleaseNotes: Optional[str] = None
    Authors: str
    ProjectType: str
    Tags: str
    IsCompiled: bool
    LicenseUrl: Optional[str] = None
    ProjectUrl: Optional[str] = None
    Id: str
    ResourceTags: List[ResourceTag]

class InputArguments(BaseModel):
    # Assuming a structure for InputArguments; adjust as necessary.
    # Example structure with a generic 'data' field; replace with actual fields.
    data: Optional[Any] = None

class OutputArguments(BaseModel):
    # Assuming a structure for OutputArguments; adjust as necessary.
    # Example structure with a generic 'data' field; replace with actual fields.
    data: Optional[Any] = None

class PackageArguments(BaseModel):
    Input: Optional[InputArguments] = None
    Output: Optional[OutputArguments] = None

    @validator('Input', 'Output', pre=True)
    def parse_arguments(cls, v):
        if v == '[]':
            return None  # Or return an empty instance, depending on your needs
        return parse_obj_as(InputArguments if cls.__fields__['Input'] == v else OutputArguments, v)


class Package(BaseModel):
    Key: str
    ProcessKey: str
    ProcessVersion: str
    IsLatestVersion: bool
    IsProcessDeleted: bool
    Description: Optional[str] = None
    Name: str
    EnvironmentId: Optional[str] = None
    EnvironmentName: str
    EntryPointId: int
    EntryPointPath: Optional[str] = None
    InputArguments: Optional[str] = None  # Update based on new structure if needed
    ProcessType: str
    SupportsMultipleEntryPoints: bool
    RequiresUserInteraction: bool
    IsAttended: bool
    IsCompiled: bool
    AutomationHubIdeaUrl: Optional[str] = None
    AutoUpdate: bool
    HiddenForAttendedUser: bool
    FeedId: str
    JobPriority: str
    SpecificPriorityValue: int
    OrganizationUnitId: int
    OrganizationUnitFullyQualifiedName: str
    TargetFramework: str
    RobotSize: Optional[str] = None
    AutoCreateConnectedTriggers: bool
    RemoteControlAccess: str
    LastModificationTime: Optional[datetime] = None
    LastModifierUserId: Optional[int] = None
    CreationTime: datetime
    CreatorUserId: int
    Id: int
    Arguments: PackageArguments
    ProcessSettings: Optional[str] = None
    VideoRecordingSettings: Optional[str] = None
    Tags: List[str]
    ResourceOverwrites: List[Dict[str, Any]]

class ProcessArguments(BaseModel):
    Input: Optional[InputArguments] = None
    Output: Optional[OutputArguments] = None

class Process(BaseModel):
    IsActive: bool
    SupportsMultipleEntryPoints: bool
    MainEntryPointPath: str
    RequiresUserInteraction: bool
    IsAttended: bool
    TargetFramework: str
    Title: str
    Version: str
    Key: str
    Description: str
    Published: datetime
    IsLatestVersion: bool
    OldVersion: Optional[str] = None
    ReleaseNotes: Optional[str] = None
    Authors: str
    ProjectType: str
    Tags: str
    IsCompiled: bool
    LicenseUrl: Optional[str] = None
    ProjectUrl: Optional[str] = None
    Id: str
    Arguments: ProcessArguments
    ResourceTags: List[dict] = Field(default_factory=list)

class Folder(BaseModel):
    Key: str
    DisplayName: str
    FullyQualifiedName: str
    FullyQualifiedNameOrderable: str
    Description: Optional[str] = None
    FolderType: str
    ProvisionType: str
    PermissionModel: str
    ParentId: Optional[str] = None
    ParentKey: Optional[str] = None
    IsActive: bool
    FeedType: str
    Id: int
    processes: Optional[List[Process]] = None

class Tenant(BaseModel):
    name: str
    id: str
    color: Optional[str] = None
    enabledServices: List[str]
    isCanaryTenant: bool
    packages: Optional[List[Package]] = None
    libraries: Optional[List[Library]] = None
    folders: Optional[List[Folder]] = None
    machines: Optional[List[Machine]] = None
    #Role

class Organization(BaseModel):
    uuid: Optional[UUID] = None
    name: str
    accountType: Optional[str] = None
    licenseCode: Optional[str] = None
    country: Optional[str] = None
    partitionGlobalId: Optional[UUID] = None
    applications: Optional[List[Application]] = None
    tenants: Optional[List[Tenant]] = None

class TokenInfo(BaseModel):
    access_token: str
    grant_type: str  # Identifies the grant type used to obtain the token
    refresh_token: Optional[str] = None
    token_expires: int  # Consider storing as datetime or timestamp for easier expiration handling
    token_type: str = "Bearer"

#SecureDumpModel extends BaseModel to enhance data security by masking sensitive fields for logging.
class UiPathCloudOauth2(SecureDumpModel):
    name: str
    client_id: str
    client_secret: str
    grant_types: List[str] = Field(..., min_items=1, max_items=3)
    scope: str
    redirect_url: str = None
    refresh_token: str = None
    access_token: str = None
    token_expires: int = 0
    access_tokens: List[TokenInfo] = []

    @validator('grant_types', each_item=True)
    def check_grant_type_valid(cls, v): #pylint: disable=no-self-argument
        if v not in VALID_GRANT_TYPES:
            raise ValueError(f'Invalid grant type: {v}. Must be one of {VALID_GRANT_TYPES}')
        return v









class Feed(BaseModel):
    name: str
    purpose: str
    isShared: bool
    isPublic: bool
    isExternal: bool
    feedUrl: HttpUrl
    publishUrl: HttpUrl
    authenticationType: str
    apiKey: Optional[str] = None
    basicUserName: Optional[str] = None
    basicPassword: Optional[str] = None
    folderId: Optional[int] = None
    supportedProjectTypes: List[str]
    id: str

class Feeds(List[Feed]):
    pass




