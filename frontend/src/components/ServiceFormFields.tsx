import {useState} from 'react';
import {FileText,UploadSimple,XCircle,DownloadSimple} from '@phosphor-icons/react';
import type {FormSchema,FormAnswers,Attachment} from '../api/types';
import {api} from '../api/client';

export function ServiceFormFields({
  schema,
  answers,
  onChange,
  readOnly = false
}: {
  schema: FormSchema;
  answers: FormAnswers;
  onChange?: (next: FormAnswers) => void;
  readOnly?: boolean;
}) {
  const [uploadingField, setUploadingField] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<Record<string, string>>({});

  function change(key: string, value: string | number | boolean | Record<string, any> | undefined) {
    const next = {...answers};
    if (value === undefined) delete next[key];
    else next[key] = value;
    onChange?.(next);
  }

  async function handleFileUpload(fieldKey: string, file: File) {
    setUploadingField(fieldKey);
    setUploadError(prev => ({...prev, [fieldKey]: ''}));
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('field_key', fieldKey);
      const res = await api<Attachment>('/attachments/upload', {
        method: 'POST',
        body: formData
      });
      change(fieldKey, {
        id: res.id,
        filename: res.filename,
        size_bytes: res.size_bytes
      });
    } catch (err) {
      setUploadError(prev => ({...prev, [fieldKey]: (err as Error).message}));
    } finally {
      setUploadingField(null);
    }
  }

  if (readOnly) {
    return (
      <dl className="service-answers">
        {schema.fields.map(field => {
          const val = answers[field.key];
          let displayNode = <span>—</span>;
          if (field.type === 'file' && val) {
            const fileObj = typeof val === 'object' && val !== null ? val as Record<string, any> : null;
            const fileId = fileObj?.id ?? (typeof val === 'number' ? val : null);
            const fileName = fileObj?.filename ?? (typeof val === 'string' ? val : 'Berkas Terunggah');
            displayNode = fileId ? (
              <a
                href={`/api/v1/attachments/${fileId}/download`}
                target="_blank"
                rel="noreferrer"
                className="file-download-link"
              >
                <FileText size={16} />
                <span>{fileName}</span>
                <DownloadSimple size={14} />
              </a>
            ) : (
              <span>{fileName}</span>
            );
          } else if (val !== undefined) {
            displayNode = <span>{typeof val === 'boolean' ? (val ? 'Ya' : 'Tidak') : String(val)}</span>;
          }

          return (
            <div key={field.key}>
              <dt>{field.label}</dt>
              <dd>{displayNode}</dd>
            </div>
          );
        })}
      </dl>
    );
  }

  return (
    <div className="service-fields">
      {schema.fields.map(field => {
        const id = 'service-answer-' + field.key;
        const value = answers[field.key];

        if (field.type === 'file') {
          const fileObj = typeof value === 'object' && value !== null ? value as Record<string, any> : null;
          const fileName = fileObj?.filename ?? (typeof value === 'string' ? value : null);
          const isUploading = uploadingField === field.key;
          const errorMsg = uploadError[field.key];

          return (
            <div className="service-field file-field" key={field.key}>
              <label htmlFor={id}>
                {field.label}
                {field.required && <span aria-hidden="true">*</span>}
              </label>
              {fileName ? (
                <div className="uploaded-file-tag">
                  <FileText size={18} />
                  <span className="file-name">{fileName}</span>
                  <button
                    type="button"
                    className="remove-file-btn"
                    title="Ganti / Hapus berkas"
                    onClick={() => change(field.key, undefined)}
                  >
                    <XCircle size={18} />
                  </button>
                </div>
              ) : (
                <div className="file-input-wrapper">
                  <input
                    id={id}
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                    required={field.required && !value}
                    disabled={isUploading}
                    onChange={e => {
                      const file = e.target.files?.[0];
                      if (file) handleFileUpload(field.key, file);
                    }}
                  />
                  <span className="file-hint">
                    {isUploading ? 'Mengunggah dokumen…' : 'Pilih file (PDF, JPG, PNG, DOCX maks. 10MB)'}
                  </span>
                </div>
              )}
              {errorMsg && <p className="field-error">{errorMsg}</p>}
            </div>
          );
        }

        return (
          <div className="service-field" key={field.key}>
            <label htmlFor={id}>
              {field.label}
              {field.required && <span aria-hidden="true">*</span>}
            </label>
            {field.type === 'textarea' ? (
              <textarea
                required={field.required}
                id={id}
                rows={3}
                maxLength={field.max_length ?? 5000}
                minLength={field.min_length ?? undefined}
                value={typeof value === 'string' ? value : ''}
                onChange={e => change(field.key, e.target.value)}
              />
            ) : field.type === 'select' ? (
              <select
                required={field.required}
                id={id}
                value={typeof value === 'string' ? value : ''}
                onChange={e => change(field.key, e.target.value)}
              >
                <option value="">Pilih jawaban</option>
                {field.options?.map(option => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            ) : field.type === 'checkbox' ? (
              <input
                id={id}
                type="checkbox"
                checked={value === true}
                onChange={e => change(field.key, e.target.checked)}
              />
            ) : (
              <input
                required={field.required}
                id={id}
                type={field.type === 'text' ? 'text' : field.type}
                maxLength={field.max_length ?? 255}
                minLength={field.min_length ?? undefined}
                min={field.min_value ?? undefined}
                max={field.max_value ?? undefined}
                step={field.type === 'number' ? 'any' : undefined}
                value={typeof value === 'string' || typeof value === 'number' ? value : ''}
                onChange={e =>
                  change(
                    field.key,
                    field.type === 'number'
                      ? Number.isFinite(e.target.valueAsNumber)
                        ? e.target.valueAsNumber
                        : undefined
                      : e.target.value
                  )
                }
              />
            )}
          </div>
        );
      })}
      <small className="subtle">* Wajib diisi. Jawaban diperiksa sesuai versi formulir layanan.</small>
    </div>
  );
}
