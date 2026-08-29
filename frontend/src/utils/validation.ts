
export const isValidWebUrl = (urlString: string): boolean => {
    try {

        if (urlString === undefined || urlString === null)
            return false;

        if (urlString.length === 0)
            return false;

        const url = new URL(urlString);

        const hasWebProtocol = url.protocol === "http:" || url.protocol === "https:";
        const isNotLocal = url.hostname !== "localhost";
        const isNotLocalLookup = url.hostname !== "127.0.0.1";

        return hasWebProtocol && isNotLocal && isNotLocalLookup;

    } catch {
        return false;
    }
}

export const emailRules = [
    (value: string) => !!value || 'Email is required',
    (value: string) => /.+@.+\..+/.test(value) || 'Enter a valid email address',
]

export const usernameRules = [
    (value: string) => !!value || 'Username is required',
    (value: string) => value.length >= 1 || 'Username is required',
    (value: string) => value.length <= 255 || 'Username must be 255 characters or fewer',
]

export const passwordRules = [
    (value: string) => !!value || 'Password is required',
    (value: string) => value.length >= 8 || 'Password must be at least 8 characters',
    (value: string) => value.length <= 255 || 'Password must be 255 characters or fewer',
    (value: string) => /[A-Z]/.test(value) || 'Password must contain at least one uppercase letter',
    (value: string) => /[a-z]/.test(value) || 'Password must contain at least one lowercase letter',
    (value: string) => /\d/.test(value) || 'Password must contain at least one digit',
    (value: string) => /[^\w\s]/.test(value) || 'Password must contain at least one special character',
]

export const confirmPasswordRules = (password: string | null) => [
    (value: string) => !!value || 'Please confirm your password',
    (value: string) => value === password || 'Passwords do not match',
]
export const roleNameRules = [
    (value: string) => !!value || 'Role name is required',
    (value: string) => value.length >= 1 || 'Role name is required',
    (value: string) => value.length <= 255 || 'Role name must be 255 characters or fewer',
]
export const roleDescriptionRules = [
    (value: string) => !value || value.length <= 255 || 'Role description must be 255 characters or fewer',
]

export const permissionDescriptionRules = [
    (value: string) => (!!value && value.length <= 255) || 'Permission description must be 255 characters or fewer',
]

export const permissionResourceRules = [
    (value: string) => !!value || 'Permission resource is required',
    (value: string) => value.length <= 255 || 'Permission resource must be 255 characters or fewer',
    (value: string) => (['source', 'article', 'alert', 'job', 'keyword', 'dashboard'].includes(value)) || 'Permission resource must be one of: source, article, alert, job, keyword, dashboard',
]

export const permissionActionRules = [
    (value: string) => (!!value && value.length <= 255) || 'Permission action must be 255 characters or fewer',
    (value: string) => (['create', 'read', 'update', 'delete', 'run'].includes(value)) || 'Permission action can only contain letters, numbers, underscores, and hyphens',
]

export const permissionScopeRules = [
    (value: string) => (!!value && value.length <= 255) || 'Permission scope must be 255 characters or fewer',
    (value: string) => (['*', 'own', 'any'].includes(value)) || 'Permission scope can only contain letters, numbers, underscores, and hyphens',
]
