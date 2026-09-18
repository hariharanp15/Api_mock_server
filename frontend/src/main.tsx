import { StrictMode } from 'react'; import { createRoot } from 'react-dom/client'; import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'; import App from './App';
createRoot(document.getElementById('root')!).render(<StrictMode><ThemeProvider theme={createTheme({palette:{mode:'dark'}})}><CssBaseline/><App/></ThemeProvider></StrictMode>);
