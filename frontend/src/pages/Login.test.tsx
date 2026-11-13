import {Theme} from '@radix-ui/themes';
import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';
import {expect, it, vi} from 'vitest';
import {Login} from './Login';
import {bootstrapCsrf} from '../api/client';

vi.mock('../auth/AuthProvider', () => ({useAuth: () => ({setUser: vi.fn()})}));
vi.mock('../api/client', () => ({api: vi.fn(), bootstrapCsrf: vi.fn()}));

it('memeriksa dan menyembunyikan password tanpa mengirim pendaftaran', async () => {
 const user = userEvent.setup();
 render(<Theme><MemoryRouter><Login register/></MemoryRouter></Theme>);

 await user.type(screen.getByLabelText('Nama lengkap'), 'Warga Demo');
 await user.type(screen.getByLabelText('Email'), 'warga@example.com');
 const password = screen.getByLabelText('Password');
 await user.type(password, 'PasswordDemo123');
 expect(password).toHaveAttribute('type', 'password');

 await user.tab();
 expect(screen.getByRole('button', {name: 'Tampilkan password'})).toHaveFocus();
 await user.keyboard('{Enter}');
 expect(password).toHaveAttribute('type', 'text');
 expect(password).toHaveValue('PasswordDemo123');

 await user.click(screen.getByRole('button', {name: 'Sembunyikan password'}));
 expect(password).toHaveAttribute('type', 'password');
 expect(password).toHaveValue('PasswordDemo123');
 expect(bootstrapCsrf).not.toHaveBeenCalled();
});
