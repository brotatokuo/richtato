const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface MeasurementData {
  id: number;
  time: string;
  data_source?: string;
  tags?: Record<string, string | number | boolean>;
  other_measurements?: Record<string, string | number | boolean>;
  [key: string]:
    | string
    | number
    | boolean
    | undefined
    | Record<string, string | number | boolean>; // For dynamic measurement fields
}

export interface EquipmentMeasurement {
  id: string;
  name: string;
  serial_number?: string;
  make?: string;
  model?: string;
  operational_status: string;
  electrical_system: string;
  asset_type: string;
  latest_measurement?: MeasurementData;
}

export interface LatestMeasurementsResponse {
  facility_id: string;
  facility_name: string;
  total_equipment: number;
  equipment_with_measurements: number;
  equipment_without_measurements: number;
  measurements: EquipmentMeasurement[];
}

export const measurementsApi = {
  async getLatestMeasurements(
    facilityId: string
  ): Promise<LatestMeasurementsResponse> {
    const response = await fetch(
      `${API_BASE_URL}/measurements/facility/${facilityId}/latest-measurements/`,
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
      if (response.status === 404) {
        throw new Error('Facility not found');
      }
      throw new Error('Failed to fetch latest measurements');
    }

    const data = await response.json();
    return data.data; // The API returns data wrapped in a response object
  },
};
