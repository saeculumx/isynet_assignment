import { Component, OnInit } from '@angular/core';
import { ApiService } from './api.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgChartsModule } from 'ng2-charts';
import { ChartData, ChartType } from 'chart.js';
import { isPlatformBrowser } from '@angular/common';
import { PLATFORM_ID, Inject } from '@angular/core';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, NgChartsModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'frontend | Isynet | Huiyu Xie';
  searchResults: any[] = [];
  columns: string[] = [];
  selectedColumns: string[] = [];
  filters: { field: string; operator: string; value: string }[] = [
    { field: '', operator: 'contains', value: '' }
  ];
  currentPage: number = 1;
  totalResults: number = 0;
  totalPages: number = 0;
  searchTime: number = 0;
  sortColumn: string = '';
  sortDirection: 'asc' | 'desc' = 'asc';
  amountFilter: string = 'no_filter';

  xField: string = 'ForeignCountry';
  yField: string = 'Total_Amount_INV_FC';
  aggFunc: string = 'sum';
  chartType: ChartType = 'pie';

  chartData: ChartData<'bar' | 'pie' | 'line', number[], string> = {
    labels: [],
    datasets: []
  };

  isBrowser = false;

  constructor(@Inject(PLATFORM_ID) private platformId: Object, private apiService: ApiService) {
    this.isBrowser = isPlatformBrowser(this.platformId);
  }

  ngOnInit(): void {
    this.getMetaData();
    this.search();
    this.loadAggregationChart();
  }

  getMetaData(): void {
    this.apiService.getMeta().subscribe(data => {
      this.columns = data.columns;

      const defaultCols = [
        'BillNO',
        'HSCode',
        'Product',
        'Unit',
        'Quantity',
        'Item_Rate_INR',
        'Total_Amount_INV_FC',
        'Currency',
        'ForeignCountry',
        'ForeignCompany',
        'IndianCompany'
      ];

      this.selectedColumns = this.columns.filter(col => defaultCols.includes(col));
      this.filters[0].field = this.columns.includes('Product') ? 'Product' : this.columns[0];
    });
  }

  addFilter(): void {
    this.filters.push({ field: this.columns[0], operator: 'contains', value: '' });
  }

  removeFilter(index: number): void {
    this.filters.splice(index, 1);
  }

  search(): void {
    this.apiService.search(
      this.filters,
      this.currentPage,
      this.sortColumn,
      this.sortDirection,
      this.amountFilter
    ).subscribe(data => {
      this.searchResults = data.data;
      this.searchTime = data.search_time;
      this.totalResults = data.total_results;
      this.totalPages = data.total_pages;
    });
  }

  resetFilters(): void {
    this.filters = [{ field: this.columns[0], operator: 'contains', value: '' }];
    this.selectedColumns = [...this.columns];
    this.sortColumn = '';
    this.sortDirection = 'asc';
    this.amountFilter = 'no_filter';
    this.currentPage = 1;
    this.search();
  }

  toggleColumn(column: string, event: Event): void {
    const isChecked = (event.target as HTMLInputElement).checked;
    if (isChecked) {
      this.selectedColumns.push(column);
    } else {
      const index = this.selectedColumns.indexOf(column);
      if (index > -1) {
        this.selectedColumns.splice(index, 1);
      }
    }
  }

  selectAllColumns(): void {
    this.selectedColumns = [...this.columns];
  }

  deselectAllColumns(): void {
    this.selectedColumns = [];
  }

  sortByColumn(column: string): void {
    if (this.sortColumn === column) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortColumn = column;
      this.sortDirection = 'asc';
    }
    this.currentPage = 1;
    this.search();
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.search();
    }
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.search();
    }
  }

  loadAggregationChart(): void {
    if (!this.xField || !this.yField) return;

    this.apiService.getAggregate(this.filters, this.xField, this.yField, this.aggFunc)
      .subscribe(data => {
        this.chartData = {
          labels: Object.keys(data),
          datasets: [
            {
              data: Object.values(data),
              label: `${this.aggFunc} of ${this.yField} by ${this.xField}`
            }
          ]
        };
      });
  }
}
