import {BrowserRouter,Routes,Route,Navigate,useLocation} from 'react-router-dom';
import {useAuth} from './auth/AuthProvider';
import {AppShell} from './components/AppShell';
import {Home} from './pages/Home';
import {NotFound} from './pages/NotFound';
import {Login} from './pages/Login';
import {Dashboard} from './pages/Dashboard';
import {Requests,NewRequest} from './pages/Requests';
import {RequestDetail} from './pages/RequestDetail';
import {Agencies} from './pages/Agencies';
import {WorkflowRoutes} from './pages/WorkflowRoutes';
import {AuditLogs} from './pages/AuditLogs';
import {Staff} from './pages/Staff';
import {ModelEvaluation} from './pages/ModelEvaluation';
import {Profile} from './pages/Profile';
import type {Role} from './api/types';
import type {ReactNode} from 'react';
function Guard({roles,children}:{roles?:Role[];children:ReactNode}){const {user,loading}=useAuth(),location=useLocation();if(loading)return <div className="state" role="status">Menyiapkan ruang layanan…</div>;if(!user)return <Navigate to="/login" state={{from:location.pathname}} replace/>;if(roles&&!roles.includes(user.role))return <Navigate to="/app" replace/>;return children}
export function App(){return <BrowserRouter><a className="skip-link" href="#main-content" onClick={()=>document.getElementById("main-content")?.focus()}>Lompat ke konten</a><Routes><Route path="/" element={<Home/>}/><Route path="/login" element={<Login/>}/><Route path="/register" element={<Login register/>}/><Route path="/app" element={<Guard><AppShell/></Guard>}><Route index element={<Dashboard/>}/><Route path="profile" element={<Profile/>}/><Route path="requests" element={<Requests/>}/><Route path="requests/new" element={<Guard roles={['citizen']}><NewRequest/></Guard>}/><Route path="requests/:id" element={<RequestDetail/>}/><Route path="agencies" element={<Guard roles={['admin']}><Agencies/></Guard>}/><Route path="workflow" element={<Guard roles={['admin']}><WorkflowRoutes/></Guard>}/><Route path="audit" element={<Guard roles={['admin']}><AuditLogs/></Guard>}/><Route path="staff" element={<Guard roles={['admin']}><Staff/></Guard>}/><Route path="model" element={<Guard roles={['admin']}><ModelEvaluation/></Guard>}/></Route><Route path="*" element={<NotFound/>}/></Routes></BrowserRouter>}
