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

  private mapBrokerResponse(data: unknown): NEVDISVehicle {
    const body = data as Record<string, unknown>;
    return {
      plate: (body.registration_number as string) || (body.plate as string),
      state: (body.jurisdiction as string) || (body.state as string),
      rego_status: (body.registration_status as string) || (body.status as string),
      rego_expiry: (body.registration_expiry as string) || (body.expiry as string),
      make: body.make as string,
      model: body.model as string,
      year: Number.parseInt((body.year_of_manufacture as string) || (body.year as string), 10),
      colour: (body.colour as string) || (body.color as string),
      body_type: body.body_type as string,
      vin: body.vin as string,
      engine_number: body.engine_number as string,
      stolen: body.stolen_flag === true || body.stolen === 'Y',
      stolen_jurisdiction: body.stolen_jurisdiction as string,
      stolen_date: body.stolen_date as string,
      wovr_status: (body.wovr_status as string) || 'NOT_LISTED',
      wovr_type: body.wovr_type as string,
      ppsr_encumbered: body.ppsr_encumbered === true || body.ppsr === 'Y',
    };
  }
}
