const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface Facility {
  id: string;
  name: string;
  address?: string;
  contact_person?: string;
  contact_person_name?: string;
  organization: string;
  organization_name?: string;
  created_at: string;
  updated_at: string;
}

export interface FacilityDAGData {
  nodes: ReactFlowNode[];
  edges: ReactFlowEdge[];
  facility_id: string;
  facility_name: string;
  total_assets: number;
  total_connections: number;
}

export interface ReactFlowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    asset_type: string;
    operational_status: string;
    electrical_system: string;
    serial_number?: string;
    make?: string;
    model?: string;
    asset_tag?: string;
    location?: string;
  };
}

export interface ReactFlowEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  data: {
    connection_type: string;
    notes?: string;
    is_active: boolean;
    is_powered: boolean;
  };
}

export const facilityApi = {
  async getFacilities(): Promise<Facility[]> {
    const response = await fetch(`${API_BASE_URL}/facilities/`, {
      headers: {
        Authorization: `Token ${localStorage.getItem('auth_token')}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token is invalid, clear it
        localStorage.removeItem('auth_token');
        throw new Error('Authentication required. Please log in again.');
      }
      throw new Error('Failed to fetch facilities');
    }

    const data = await response.json();
    return data.results || data; // Handle both paginated and non-paginated responses
  },

  async getFacilityDAG(facilityId: string): Promise<FacilityDAGData> {
    const response = await fetch(
      `${API_BASE_URL}/connections/facility_dag/?facility_id=${facilityId}`,
      {
        headers: {
          Authorization: `Token ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      if (response.status === 401) {
        // Token is invalid, clear it
        localStorage.removeItem('auth_token');
        throw new Error('Authentication required. Please log in again.');
      }
      throw new Error('Failed to fetch facility DAG');
    }

    return response.json();
  },
};
