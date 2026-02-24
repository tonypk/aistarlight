import { client } from './client'

export interface LoginData {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  full_name: string
  company_name: string
}

export interface Company {
  tenant_id: string
  company_name: string
  role: string
  tin_number: string | null
}

export const authApi = {
  login: (data: LoginData) => client.post('/auth/login', data),
  register: (data: RegisterData) => client.post('/auth/register', data),
  me: () => client.get('/auth/me'),
  logout: (refreshToken: string) => client.post('/auth/logout', { refresh_token: refreshToken }),
  generateApiKey: () => client.post('/auth/api-key'),
  listCompanies: () => client.get('/auth/companies'),
  switchCompany: (tenantId: string) => client.post('/auth/switch-company', { tenant_id: tenantId }),
  inviteMember: (email: string, role: string) => client.post('/auth/invite', { email, role }),
}
