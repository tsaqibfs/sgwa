import {useState} from 'react';
import {useData} from '../api/useData';
import type {Agency} from '../api/types';
import {PageState} from './PageState';

type Forecast = {
 agency: {id: number; name: string};
 history_days: number;
 minimum_history_days: number;
 history: {date: string; count: number}[];
 forecast: {date: string; estimate: number}[];
 method: 'same_weekday' | 'moving_average' | null;
 evaluation: {days: number; baseline_mae: number; moving_average_mae: number} | null;
};

const number = (value: number) => value.toLocaleString('id-ID', {maximumFractionDigits: 2});
const day = (value: string) => new Date(value + 'T00:00:00Z').toLocaleDateString(
 'id-ID', {day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC'}
);

function ForecastData({agencyId}: {agencyId: number}) {
 const {data, error, loading, reload} = useData<Forecast>('/reports/forecast?agency_id=' + agencyId);
 return <>
  <PageState loading={loading} error={error} reload={reload}/>
  {data && !error && <>
   <p><strong>{data.agency.name}</strong> · {data.history_days} hari riwayat</p>
   {data.evaluation ? <>
    <p>Metode terpilih: {data.method === 'same_weekday' ? 'hari yang sama pada minggu sebelumnya' : 'rata-rata tujuh hari sebelumnya'}.</p>
    <p className="subtle">Pada uji ulang {data.evaluation.days} hari terakhir, rata-rata selisih dari jumlah aktual adalah {number(data.evaluation.baseline_mae)} permohonan per hari untuk metode hari yang sama dan {number(data.evaluation.moving_average_mae)} untuk metode rata-rata tujuh hari.</p>
    <div className="table-scroll"><table>
     <caption>Prakiraan tujuh hari (WIB)</caption>
     <thead><tr><th scope="col">Tanggal</th><th scope="col">Perkiraan permohonan</th></tr></thead>
     <tbody>{data.forecast.map(point => <tr key={point.date}><th scope="row">{day(point.date)}</th><td>{number(point.estimate)}</td></tr>)}</tbody>
    </table></div>
   </> : <p>Riwayat belum cukup untuk membuat prakiraan. Diperlukan sedikitnya {data.minimum_history_days} hari kalender.</p>}
   {data.history.length > 0 && <details>
    <summary>Lihat riwayat harian</summary>
    <div className="table-scroll"><table>
     <caption>Permohonan tercatat per hari (WIB)</caption>
     <thead><tr><th scope="col">Tanggal</th><th scope="col">Jumlah permohonan</th></tr></thead>
     <tbody>{[...data.history].reverse().map(point => <tr key={point.date}><th scope="row">{day(point.date)}</th><td>{number(point.count)}</td></tr>)}</tbody>
    </table></div>
   </details>}
  </>}
 </>;
}

export function AgencyForecast({agencies, staffAgencyId}: {agencies: Agency[]; staffAgencyId?: number | null}) {
 const [selection, setSelection] = useState('');
 const agencyId = staffAgencyId === undefined ? Number(selection) : staffAgencyId;
 return <section className="panel report-table agency-forecast">
  <h2>Prakiraan volume permohonan</h2>
  <p className="subtle">Prakiraan memakai tanggal pengajuan permohonan yang tercatat untuk dinas utama maupun pendamping, hingga kemarin. Hasil uji historis membantu memilih metode, dan jumlah aktual dapat berbeda.</p>
  {staffAgencyId === undefined && <div className="report-filter-grid">
   <label>Dinas untuk prakiraan
    <select value={selection} onChange={event => setSelection(event.target.value)}>
     <option value="">Pilih dinas</option>
     {agencies.map(agency => <option key={agency.id} value={agency.id}>{agency.name}</option>)}
    </select>
   </label>
  </div>}
  {agencyId ? <ForecastData key={agencyId} agencyId={agencyId}/> : staffAgencyId === null && <p>Akun Anda belum ditugaskan ke dinas.</p>}
 </section>;
}
