export const SourceTypes = [
    {value: 0, label: 'Unknown'},
    {value: 1, label: 'News Site'},
    {value: 2, label: 'Blog'},
    {value: 3, label: 'Forum'},
    {value: 4, label: 'Social Media'},
    {value: 5, label: 'Telegram Channel'},
    {value: 6, label: 'Whatsapp Channel'},
    {value: 7, label: 'Other'},
    {value: 8, label: 'RSS'}
];

export const Statuses = [
    {value: 1, label: 'Running'},
    {value: 2, label: 'Completed'},
    {value: 3, label: 'Failed'},
    {value: 4, label: 'Waiting'},
    {value: 5, label: 'Cancelled'},
];

export const Languages = [
    {value: 'en', label: 'English'},
    {value: 'uk', label: 'Ukrainian'},
    {value: 'de', label: 'German'},
    {value: 'fr', label: 'French'},
    {value: 'es', label: 'Spanish'},
    {value: 'zh', label: 'Chinese'},
    {value: 'ja', label: 'Japanese'},
    {value: 'ar', label: 'Arabic'},
    {value: 'pt', label: 'Portuguese'},
    {value: 'hi', label: 'Hindi'},
    {value: 'ru', label: 'Russian'},
    {value: 'other', label: 'Other'},
];

export enum SourseType {
    Unknown = 0,
    NewsSite = 1,
    Blog = 2,
    Forum = 3,
    SocialMedia = 4,
    TelegramChannel = 5,
    WhatsappChannel = 6,
    Other = 7,
    RSS = 8,

}

export type JobStatus = 'RUNNING' | 'COMPLETED' | 'FAILED' | 'WAITING' | 'CANCELED' | 'CANCELLED' | string

export enum Status {
    Running = 1,
    Completed = 2,
    Failed = 3,
    Waiting = 4,
    Cancelled = 5,
}


export interface SourceItem {
    id: string
    name: string
    base_url: string
    language: string
    source_type: SourseType
    crawler_key: string
    is_enabled: boolean
    scrape_interval_minutes: number
}

// Monitored keywords
export interface KeywordItem {
    id: string
    keyword: string
    is_enabled: boolean
}

export interface JobItem {
    id: string
    source_id: string
    status: Status
    started_at: string
    finished_at: string | null
    articles_found: number
    articles_created: number
    error_message: string | null
}

export interface SearchHit {
    article_id: string
    title: string
    url: string
    published_at: string | null
    source_name: string
    excerpt: string | null
    score: number | null
    is_alert: boolean
}

export interface CrawlerTypeItem {
    key: string
    title: string
    description: string
}

export interface DashboardStats {
    sources_total: number
    sources_enabled: number
    articles_total: number
    alerts_total: number
    jobs_total: number
    keywords_total: number
    elasticsearch_document_count: number
}

export interface CreateSourcePayload {
    name: string
    base_url: string
    language: string
    source_type: SourseType
    crawler_key: string
    scrape_interval_minutes: number
    is_enabled: boolean
}

export interface ArticleItem {
    id: string
    source_id: string
    url: string
    title: string
    author: string | null
    published_at: string | null
    fetched_at: string
    content_text: string
    summary: string | null
    language: string
    is_alert: boolean
    matched_keywords_csv: string | null
}


export interface KeywordsMatchMessage { 
    id: string;
    message_type: 'KEYWORDS_MATCH' | 'JOB_UPDATE';

    article_id: string; 

    matched_keywords: string[]; 

    title: string;
    
    url: string;
    published_at: string | null;

    source_name?: string;

}


export interface JobUpdateMessage {
    id: string;
    message_type: 'KEYWORDS_MATCH' | 'JOB_UPDATE';

    job_id: string;

    status: Status;

    articles_found: number;
    articles_created: number;

    error_message: string | null;

    started_at: string;

    finished_at: string | null;

    source_id: string;
}

export type TokenType = 'access' | 'refresh';

export interface LoginCredentials {
    username: string;
    passwortd: string;
}

export interface TokenPair {
    access_token: string;
    refresh_token: string;
    access_token_exp: number;
    refresh_token_exp: number;
    token_type: string;
}

export interface RefreshRequest {
    refresh_token: string;
}


export interface LogoutRequest {
    refresh_token: string;
}

export interface MeRequest {
    access_token: string;
}

export interface UserBase {
    email: string;
    username: string;
    is_active: boolean;
}

export interface UserCreate extends UserBase {
    password: string;
}

export interface UserUpdate extends UserBase{
}

export interface UserRead extends UserBase {
    id: string;
    is_verified: boolean;
    last_login_at: string | null;
    created_at: string;
    roles: string[];
}

export interface UserChangePassword {
    new_password: string;
    old_password: string;
}

export interface UserRoles {
    roles_ids: string[];
}

export interface AdminChangePassword {
    new_password: string;
}

export interface AdminRoleDistribution {
    role_name: string;
    user_count: number;
}

export interface AdminStats {
    total_users: number;
    active_users: number;
    recent_registrations: number;
    role_distribution: AdminRoleDistribution[];
}

export interface RoleRead {
    id: string | null;
    name: string;
    description: string;
    is_system: boolean;
    created_at: string;
    updated_at: string | null;
    permissions: PermissionRead[];
}


export interface PermissionRead {
    id: string;
    name: string;
    description: string;
    resource: string | null;
    action: string | null;
    created_at: string;

    updated_at: string | null;
}

// users managment.

export interface CreateUserDialogData {
    email: string;
    username: string;
    is_active: boolean;
    password: string;
    confirm_password: string;
}

export interface UpdateUserDialogData {
    id: string;
    email: string;
    username: string;
    is_active: boolean;
}

export interface RoleCreateUpdate {

    name: string;
    description: string;
    is_system: boolean;
}

export type PermissionResource = 'source' | 'article' | 'alert' | 'job' | 'keyword' | 'dashboard';

export type PermissionAction = 'create' | 'read' | 'update' | 'delete' | 'run';

export type PermissionScope = '*' | 'own' | 'any'; 


export interface PermissionCreateUpdate {
    description: string;
    resource: PermissionResource;
    action: PermissionAction;
    scope: PermissionScope;
}

export interface PermissionRow {
    key: string;
    id: string | null;
    description: string;
    resource: PermissionResource | null;
    action: PermissionAction | null;
    scope: PermissionScope | null;
    error: string | null;
}

