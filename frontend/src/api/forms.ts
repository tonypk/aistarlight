import { client } from './client'

export interface FormField {
  id: string
  line: string
  label: string
  editable: boolean
  required?: boolean
}

export interface FormSection {
  id: string
  name: string
  fields: FormField[]
}

export interface FormSchemaDef {
  sections: FormSection[]
}

export interface FormSchemaDetail {
  form_type: string
  name: string
  frequency: string
  version: number
  schema_def: FormSchemaDef
  calculation_rules: Record<string, string>
}

export interface FormSummary {
  form_type: string
  name: string
  frequency: string
  version?: number
}

export const formsApi = {
  list: () => client.get('/forms'),
  getSchema: (formType: string) => client.get(`/forms/${formType}`),
}
