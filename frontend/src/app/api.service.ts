import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) { }

  search(filters: any[], page: number, sort_by: string, sort_dir: string, amount_filter: string) {
    return this.http.post<any>(`${this.apiUrl}/search`, filters, {
      params: { page, sort_by, sort_dir, amount_filter }
    });
  }

  getMeta(): Observable<any> {
    return this.http.get(`${this.apiUrl}/meta`);
  }

  getAggregate(filters: any[], xField: string, yField: string, agg: string) {
  return this.http.post<any>(
    `${this.apiUrl}/aggregate?x_field=${xField}&y_field=${yField}&agg=${agg}`,
    filters
  );
  }

}
