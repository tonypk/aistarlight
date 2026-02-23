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

export const authApi = {
  login: (data: LoginData) => client.post('/auth/login', data),
  register: (data: RegisterData) => client.post('/auth/register', data),
  me: () => client.get('/auth/me'),
  generateApiKey: () => client.post('/auth/api-key'),
}
