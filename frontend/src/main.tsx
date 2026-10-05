import React from 'react';
import ReactDOM from 'react-dom/client';
import {Theme} from '@radix-ui/themes';
import '@radix-ui/themes/styles.css';
import './styles/app.css';
import {AuthProvider} from './auth/AuthProvider';
import {App} from './App';
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><Theme accentColor="jade" grayColor="sand" radius="medium" scaling="100%"><AuthProvider><App/></AuthProvider></Theme></React.StrictMode>);
