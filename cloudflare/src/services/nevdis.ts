export interface NEVDISVehicle {
  plate: string;
  state: string;
  rego_status: string;
  rego_expiry: string;
  make: string;
  model: string;
  year: number;
  colour: string;
  body_type: string;
  vin: string;
  engine_number: string;
  stolen: boolean;
  stolen_jurisdiction?: string;
  stolen_date?: string;
  wovr_status: string;
  wovr_type?: string;
  ppsr_encumbered: boolean;
}

export class NEVDISClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async lookupPlate(plate: string, state?: string): Promise<NEVDISVehicle | null> {
    try {
      const response = await fetch(`${this.baseUrl}/vehicle/plate/${plate}`, {
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
          ...(state && { 'X-State': state }),
        },
      });

      if (!response.ok) {
        console.error(`NEVDIS lookup failed: ${response.status}`);
        return null;
      }

      const data = await response.json();
      return this.mapBrokerResponse(data);
    } catch (error) {
      console.error('NEVDIS lookup error:', error);
      return null;
    }
  }

  private mapBrokerResponse(data: any): NEVDISVehicle {
    return {
      plate: data.registration_number || data.plate,
      state: data.jurisdiction || data.state,
      rego_status: data.registration_status || data.status,
      rego_expiry: data.registration_expiry || data.expiry,
      make: data.make,
      model: data.model,
      year: parseInt(data.year_of_manufacture || data.year),
      colour: data.colour || data.color,
      body_type: data.body_type,
      vin: data.vin,
      engine_number: data.engine_number,
      stolen: data.stolen_flag === true || data.stolen === 'Y',
      stolen_jurisdiction: data.stolen_jurisdiction,
      stolen_date: data.stolen_date,
      wovr_status: data.wovr_status || 'NOT_LISTED',
      wovr_type: data.wovr_type,
      ppsr_encumbered: data.ppsr_encumbered === true || data.ppsr === 'Y',
    };
  }
}
