import { request } from '@/utils/request'
import { LicenseGenerator } from '@/services/adaptiveLicense'
export const AuthApi = {
  login: async (credentials: { username: string; password: string }) => {
    const entryCredentials = {
      username: await LicenseGenerator.sqlbotEncrypt(credentials.username),
      password: await LicenseGenerator.sqlbotEncrypt(credentials.password),
    }
    return request.post<{
      data: any
      token: string
    }>('/login/access-token', entryCredentials, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
  },
  logout: (data: any) => request.post('/login/logout', data),
  info: () => request.get('/user/info'),
}
