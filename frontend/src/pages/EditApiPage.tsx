import { useEffect, useState } from 'react';
import { Alert, Box, Button, CircularProgress, FormControlLabel, MenuItem, Switch, TextField, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import client from '../api/client';

type Form = { name:string; method:string; path:string; response_delay_ms:number; is_private:boolean; auth_required:boolean };
export default function EditApiPage() {
  const { id } = useParams(); const navigate = useNavigate(); const [form,setForm] = useState<Form>(); const [error,setError] = useState(''); const set = (key:keyof Form, value:string|number|boolean) => setForm(current => current ? {...current,[key]:value} : current);
  useEffect(()=>{client.get(`/apis/${id}`).then(r=>setForm(r.data)).catch(()=>setError('API not found or you do not have access.'));},[id]);
  const submit=async(e:React.FormEvent)=>{e.preventDefault();if(!form)return;try{await client.patch(`/apis/${id}`,form);navigate('/apis')}catch(err:any){setError(err.response?.data?.detail ?? 'Could not save changes.')}};
  if (!form) return <Box textAlign="center" p={5}>{error?<Alert severity="error">{error}</Alert>:<CircularProgress/>}</Box>;
  return <Box component="form" onSubmit={submit} maxWidth={650}><Typography variant="h4" gutterBottom>Edit API</Typography>{error&&<Alert severity="error">{error}</Alert>}<TextField label="Name" fullWidth required margin="normal" value={form.name} onChange={e=>set('name',e.target.value)}/><TextField select label="HTTP method" fullWidth margin="normal" value={form.method} onChange={e=>set('method',e.target.value)}>{['GET','POST','PUT','PATCH','DELETE'].map(x=><MenuItem value={x} key={x}>{x}</MenuItem>)}</TextField><TextField label="Endpoint path" fullWidth required margin="normal" value={form.path} onChange={e=>set('path',e.target.value)}/><TextField label="Response delay (ms)" type="number" fullWidth margin="normal" value={form.response_delay_ms} onChange={e=>set('response_delay_ms',Number(e.target.value))}/><FormControlLabel control={<Switch checked={form.is_private} onChange={e=>set('is_private',e.target.checked)}/>} label="Private API"/><FormControlLabel control={<Switch checked={form.auth_required} onChange={e=>set('auth_required',e.target.checked)}/>} label="Require JWT on mock request"/><Box mt={2} display="flex" gap={1}><Button type="submit" variant="contained">Save changes</Button><Button onClick={()=>navigate('/apis')}>Cancel</Button></Box></Box>;
}
