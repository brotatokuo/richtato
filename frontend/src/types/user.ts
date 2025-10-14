/**
 * User role hierarchy as defined in the Django backend
 * Based on the CLAUDE.md documentation:
 * Super Admin → Org Admin → Facility Manager → Operator → Viewer → Maintenance
 */
export type UserRole =
  | 'super_admin'
  | 'org_admin'
  | 'facility_manager'
  | 'operator'
  | 'viewer'
  | 'maintenance';

/**
 * Role display names and descriptions for UI
 */
export const ROLE_DEFINITIONS: Record<
  UserRole,
  {
    label: string;
    description: string;
    level: number;
  }
> = {
  super_admin: {
    label: 'Super Admin',
    description: 'Full system access across all organizations',
    level: 6,
  },
  org_admin: {
    label: 'Organization Admin',
    description: 'Full access within organization',
    level: 5,
  },
  facility_manager: {
    label: 'Facility Manager',
    description: 'Manage facilities within organization',
    level: 4,
  },
  operator: {
    label: 'Operator',
    description: 'Operate systems and equipment',
    level: 3,
  },
  viewer: {
    label: 'Viewer',
    description: 'View-only access to systems',
    level: 2,
  },
  maintenance: {
    label: 'Maintenance',
    description: 'Access maintenance logs and schedules',
    level: 1,
  },
};

/**
 * User interface matching Django User model structure
 */
export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  organization_id: string;
  organization_name?: string;
  facility_ids?: string[];
  is_active: boolean;
  last_login?: string;
  date_joined: string;
  created_at: string;
  updated_at: string;
}

/**
 * Create user request payload
 */
export interface CreateUserRequest {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  organization_id: string;
  facility_ids?: string[];
  password: string;
  is_active?: boolean;
}

/**
 * Update user request payload
 */
export interface UpdateUserRequest {
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  role?: UserRole;
  organization_id?: string;
  facility_ids?: string[];
  is_active?: boolean;
}

/**
 * Organization interface for user assignment
 */
export interface Organization {
  id: string;
  name: string;
  description?: string;
}

/**
 * Facility interface for user assignment
 */
export interface Facility {
  id: string;
  name: string;
  organization_id: string;
  location?: string;
}
