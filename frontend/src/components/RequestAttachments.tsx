import {useState} from 'react';
import {Button, Dialog} from '@radix-ui/themes';
import {Files, UploadSimple, DownloadSimple, Trash, FileText, CheckCircle} from '@phosphor-icons/react';
import type {Attachment, WorkflowTask, Agency} from '../api/types';
import {useAuth} from '../auth/AuthProvider';
import {api} from '../api/client';

interface RequestAttachmentsProps {
  requestId: number;
  attachments?: Attachment[];
  workflows?: WorkflowTask[];
  allAgencies?: Agency[];
  isClosed?: boolean;
  onReload: () => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

export function RequestAttachments({
  requestId,
  attachments = [],
  workflows = [],
  allAgencies = [],
  isClosed = false,
  onReload
}: RequestAttachmentsProps) {
  const {user} = useAuth();
  const [openUpload, setOpenUpload] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [agencyId, setAgencyId] = useState<string>('');
  const [description, setDescription] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Available agencies to choose from:
  // If staff: defaults to staff's own agency.
  // If citizen/admin: shows assigned workflow agencies, or can choose from all active agencies.
  const assignedAgencies = workflows.map(w => ({
    id: w.agency_id,
    name: w.agency_name
  }));

  const candidateAgencies = assignedAgencies.length > 0 
    ? assignedAgencies 
    : allAgencies.filter(a => a.active);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setError('Silakan pilih berkas yang ingin diunggah.');
      return;
    }
    setBusy(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (agencyId) {
        formData.append('agency_id', agencyId);
      } else if (user?.role === 'staff' && user.agency_id) {
        formData.append('agency_id', String(user.agency_id));
      }
      if (description.trim()) {
        formData.append('description', description.trim());
      }

      await api(`/requests/${requestId}/attachments`, {
        method: 'POST',
        body: formData
      });

      setOpenUpload(false);
      setFile(null);
      setDescription('');
      setAgencyId('');
      onReload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(attachmentId: number) {
    if (!confirm('Apakah Anda yakin ingin menghapus berkas ini?')) return;
    setDeletingId(attachmentId);
    try {
      await api(`/attachments/${attachmentId}`, {method: 'DELETE'});
      onReload();
    } catch (err) {
      alert((err as Error).message);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className="panel attachments-panel">
      <div className="section-heading">
        <div className="heading-with-badge">
          <h2>Berkas Pendukung Berdasarkan Dinas</h2>
          <span className="count-badge">{attachments.length} Berkas</span>
        </div>
        {!isClosed && (
          <Button variant="soft" onClick={() => setOpenUpload(true)}>
            <UploadSimple size={16} />
            Unggah Berkas Baru
          </Button>
        )}
      </div>

      <p className="subtle">
        Dokumen persyaratan dan berkas pendukung yang dikaitkan dengan dinas pelaksana permohonan.
      </p>

      {attachments.length === 0 ? (
        <div className="empty-attachments">
          <Files size={32} />
          <p>Belum ada berkas pendukung yang diunggah untuk permohonan ini.</p>
        </div>
      ) : (
        <div className="attachments-list">
          {attachments.map(att => {
            const canDelete =
              !isClosed && (user?.role === 'admin' || att.uploaded_by === user?.id);

            return (
              <div key={att.id} className="attachment-card">
                <div className="attachment-icon">
                  <FileText size={24} />
                </div>
                <div className="attachment-info">
                  <div className="attachment-header">
                    <strong className="attachment-filename">{att.filename}</strong>
                    <span className="agency-tag">{att.agency_name}</span>
                  </div>
                  {att.description && (
                    <p className="attachment-desc">{att.description}</p>
                  )}
                  <div className="attachment-meta">
                    <span>{formatSize(att.size_bytes)}</span>
                    <span>·</span>
                    <span>Diunggah oleh {att.uploader_name}</span>
                  </div>
                </div>
                <div className="attachment-actions">
                  <a
                    href={`/api/v1/attachments/${att.id}/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="download-btn"
                    title="Unduh Berkas"
                  >
                    <DownloadSimple size={16} />
                    <span>Unduh</span>
                  </a>
                  {canDelete && (
                    <Button
                      variant="ghost"
                      color="red"
                      disabled={deletingId === att.id}
                      onClick={() => handleDelete(att.id)}
                      title="Hapus Berkas"
                    >
                      <Trash size={16} />
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <Dialog.Root open={openUpload} onOpenChange={open => !busy && setOpenUpload(open)}>
        <Dialog.Content maxWidth="480px">
          <Dialog.Title>Unggah Berkas Pendukung</Dialog.Title>
          <Dialog.Description>
            Pilih berkas dokumen (PDF, Gambar JPG/PNG, atau Dokumen Word maks. 10 MB).
          </Dialog.Description>

          <form onSubmit={handleUpload} className="upload-modal-form">
            <div className="form-group">
              <label htmlFor="upload-agency">Tujuan Dinas / Persyaratan</label>
              {user?.role === 'staff' ? (
                <p className="fixed-agency-note">
                  Dinas Anda: <strong>{candidateAgencies.find(a => a.id === user.agency_id)?.name || 'Dinas Terkait'}</strong>
                </p>
              ) : (
                <select
                  id="upload-agency"
                  value={agencyId}
                  onChange={e => setAgencyId(e.target.value)}
                >
                  <option value="">Umum / Semua Dinas Terkait</option>
                  {candidateAgencies.map(a => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="upload-desc">Keterangan Dokumen (Opsional)</label>
              <input
                id="upload-desc"
                type="text"
                placeholder="Misal: KTP Asli, Formulir Verifikasi Lapangan, Izin Usaha"
                value={description}
                maxLength={200}
                onChange={e => setDescription(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="upload-file">Pilih Berkas *</label>
              <input
                id="upload-file"
                type="file"
                required
                accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                onChange={e => setFile(e.target.files?.[0] || null)}
              />
              <span className="field-hint">
                Format yang didukung: .pdf, .jpg, .jpeg, .png, .doc, .docx
              </span>
            </div>

            {error && <p className="error" role="alert">{error}</p>}

            <div className="dialog-actions">
              <Button
                type="button"
                variant="soft"
                color="gray"
                disabled={busy}
                onClick={() => setOpenUpload(false)}
              >
                Batal
              </Button>
              <Button type="submit" loading={busy} disabled={!file}>
                Unggah Berkas
              </Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Root>
    </section>
  );
}
