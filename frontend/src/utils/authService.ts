import api from '@/utils/api'

export const authService = {
  async register(email: string, username: string, fullName: string, password: string) {
    const response = await api.post('/auth/register', {
      email,
      username,
      full_name: fullName,
      password,
    })
    return response.data
  },

  async verifyEmail(token: string, password: string) {
    const response = await api.post('/auth/verify-email', {
      token,
      password,
    })
    return response.data
  },

  async login(email: string, password: string) {
    const response = await api.post('/auth/login', {
      email,
      password,
    })
    return response.data
  },

  async verifyLoginOtp(email: string, otp: string) {
    const response = await api.post('/auth/login/verify-otp', {
      email,
      otp,
    })
    return response.data
  },

  async getCurrentUser() {
    const response = await api.get('/users/me')
    return response.data
  },

  async updateProfile(data: Record<string, unknown>) {
    const response = await api.put('/users/me', data)
    return response.data
  },

  async getUser(userId: string) {
    const response = await api.get(`/users/${userId}`)
    return response.data
  },

  async blockUser(userId: string) {
    const response = await api.post(`/users/block/${userId}`)
    return response.data
  },

  async reportUser(userId: string, reason: string, description?: string) {
    const response = await api.post(`/users/report/${userId}`, {
      reason,
      description,
    })
    return response.data
  },
}
