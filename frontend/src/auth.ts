export const isAuthenticated = () => Boolean(localStorage.getItem('token'));
export const signOut = () => localStorage.removeItem('token');
