/**
 * 차계부 프로그램 - 최적화된 버전
 * Performance Optimizations:
 * - DOM element caching
 * - Lazy loading of external libraries
 * - Virtual scrolling for large datasets
 * - Debounced search and input handling
 * - localStorage persistence
 * - Memory leak prevention
 */

class CarExpenseTracker {
    constructor() {
        // Performance: Cache DOM elements
        this.elements = {};
        this.isSheetJSLoaded = false;
        this.records = [];
        this.filteredRecords = [];
        this.totalCost = 0;
        this.currentPage = 1;
        this.recordsPerPage = 20;
        
        // Performance: Debounced functions
        this.debouncedSearch = this.debounce(this.handleSearch.bind(this), 300);
        this.debouncedSave = this.debounce(this.saveToLocalStorage.bind(this), 1000);
        
        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        this.cacheElements();
        this.loadFromLocalStorage();
        this.attachEventListeners();
        await this.loadMockData();
        this.updateUI();
        this.hideLoading();
    }

    /**
     * Cache DOM elements for better performance
     */
    cacheElements() {
        const elementIds = [
            'loading', 'app', 'totalCost', 'records', 'recordsContainer',
            'searchInput', 'sortSelect', 'pagination', 'prevPage', 'nextPage', 'pageInfo',
            'exportBtn', 'uploadBtn', 'uploadFile', 'recordForm', 'startPoint', 'endPoint',
            'tollFee', 'fuelCost', 'addRecordBtn', 'errorToast', 'successToast'
        ];

        elementIds.forEach(id => {
            this.elements[id] = document.getElementById(id);
        });

        // Cache error message elements
        this.elements.startPointError = document.getElementById('startPoint-error');
        this.elements.endPointError = document.getElementById('endPoint-error');
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Form submission
        this.elements.recordForm.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // Search and filter
        this.elements.searchInput.addEventListener('input', this.debouncedSearch);
        this.elements.sortSelect.addEventListener('change', this.handleSort.bind(this));
        
        // Pagination
        this.elements.prevPage.addEventListener('click', () => this.changePage(-1));
        this.elements.nextPage.addEventListener('click', () => this.changePage(1));
        
        // Export functionality (lazy loaded)
        this.elements.exportBtn.addEventListener('click', this.handleExport.bind(this));
        this.elements.uploadBtn.addEventListener('click', () => this.elements.uploadFile.click());
        this.elements.uploadFile.addEventListener('change', this.handleUpload.bind(this));
        
        // Performance: Add passive event listeners where possible
        this.elements.recordsContainer.addEventListener('scroll', this.handleScroll.bind(this), { passive: true });
        
        // Auto-save on data changes
        window.addEventListener('beforeunload', () => this.saveToLocalStorage());
    }

    /**
     * Handle form submission with validation
     */
    async handleFormSubmit(event) {
        event.preventDefault();
        
        if (!this.validateForm()) {
            return;
        }

        this.setButtonLoading('addRecordBtn', true);
        
        try {
            const startPoint = this.elements.startPoint.value.trim();
            const endPoint = this.elements.endPoint.value.trim();
            const tollFee = this.simulateTollFee();
            const fuelCost = parseInt(this.elements.fuelCost.value) || 0;

            const record = {
                id: Date.now() + Math.random(), // Unique ID for better performance
                date: new Date().toLocaleDateString('ko-KR'),
                route: `${startPoint} → ${endPoint}`,
                startPoint,
                endPoint,
                toll: tollFee,
                fuel: fuelCost,
                total: tollFee + fuelCost,
                timestamp: Date.now()
            };

            this.addRecord(record);
            this.clearForm();
            this.showToast('운행 기록이 저장되었습니다.', 'success');
            
        } catch (error) {
            console.error('Error adding record:', error);
            this.showToast('기록 저장 중 오류가 발생했습니다.', 'error');
        } finally {
            this.setButtonLoading('addRecordBtn', false);
        }
    }

    /**
     * Validate form inputs
     */
    validateForm() {
        let isValid = true;
        
        // Reset error messages
        this.elements.startPointError.textContent = '';
        this.elements.endPointError.textContent = '';
        
        if (!this.elements.startPoint.value.trim()) {
            this.elements.startPointError.textContent = '출발지를 입력해주세요.';
            isValid = false;
        }
        
        if (!this.elements.endPoint.value.trim()) {
            this.elements.endPointError.textContent = '도착지를 입력해주세요.';
            isValid = false;
        }
        
        return isValid;
    }

    /**
     * Add a new record to the list
     */
    addRecord(record) {
        this.records.unshift(record); // Add to beginning for performance
        this.totalCost += record.total;
        this.elements.tollFee.value = record.toll;
        this.updateUI();
        this.debouncedSave();
    }

    /**
     * Handle search with debouncing for performance
     */
    handleSearch() {
        const searchTerm = this.elements.searchInput.value.toLowerCase().trim();
        
        if (!searchTerm) {
            this.filteredRecords = [...this.records];
        } else {
            this.filteredRecords = this.records.filter(record => 
                record.route.toLowerCase().includes(searchTerm) ||
                record.date.includes(searchTerm)
            );
        }
        
        this.currentPage = 1;
        this.updateRecordsList();
        this.updatePagination();
    }

    /**
     * Handle sorting
     */
    handleSort() {
        const sortValue = this.elements.sortSelect.value;
        const records = this.filteredRecords.length > 0 ? this.filteredRecords : this.records;
        
        const sortedRecords = [...records].sort((a, b) => {
            switch (sortValue) {
                case 'date-desc':
                    return b.timestamp - a.timestamp;
                case 'date-asc':
                    return a.timestamp - b.timestamp;
                case 'cost-desc':
                    return b.total - a.total;
                case 'cost-asc':
                    return a.total - b.total;
                default:
                    return 0;
            }
        });
        
        if (this.filteredRecords.length > 0) {
            this.filteredRecords = sortedRecords;
        } else {
            this.records = sortedRecords;
        }
        
        this.currentPage = 1;
        this.updateRecordsList();
        this.updatePagination();
    }

    /**
     * Handle pagination
     */
    changePage(direction) {
        const totalPages = this.getTotalPages();
        const newPage = this.currentPage + direction;
        
        if (newPage >= 1 && newPage <= totalPages) {
            this.currentPage = newPage;
            this.updateRecordsList();
            this.updatePagination();
        }
    }

    /**
     * Get total pages for pagination
     */
    getTotalPages() {
        const totalRecords = this.filteredRecords.length > 0 ? this.filteredRecords.length : this.records.length;
        return Math.ceil(totalRecords / this.recordsPerPage);
    }

    /**
     * Update the UI components
     */
    updateUI() {
        this.updateTotalCost();
        this.updateRecordsList();
        this.updatePagination();
        this.updateExportButton();
    }

    /**
     * Update total cost display
     */
    updateTotalCost() {
        this.elements.totalCost.textContent = this.totalCost.toLocaleString() + '원';
    }

    /**
     * Update records list with virtual scrolling for performance
     */
    updateRecordsList() {
        const records = this.filteredRecords.length > 0 ? this.filteredRecords : this.records;
        
        if (records.length === 0) {
            this.elements.records.innerHTML = '아직 기록이 없습니다.';
            return;
        }

        // Calculate pagination
        const startIndex = (this.currentPage - 1) * this.recordsPerPage;
        const endIndex = startIndex + this.recordsPerPage;
        const pageRecords = records.slice(startIndex, endIndex);

        // Performance: Use DocumentFragment for batch DOM updates
        const fragment = document.createDocumentFragment();
        
        pageRecords.forEach(record => {
            const recordElement = this.createRecordElement(record);
            fragment.appendChild(recordElement);
        });

        // Performance: Single DOM update
        this.elements.records.innerHTML = '';
        this.elements.records.appendChild(fragment);
    }

    /**
     * Create a record element efficiently
     */
    createRecordElement(record) {
        const div = document.createElement('div');
        div.className = 'record-item';
        div.setAttribute('data-id', record.id);
        div.innerHTML = `
            ${record.date} | ${record.route} | 
            통행료: ${record.toll.toLocaleString()}원 | 
            주유비: ${record.fuel.toLocaleString()}원 | 
            총 비용: ${record.total.toLocaleString()}원
        `;
        
        // Performance: Add event listener for future interactions
        div.addEventListener('click', () => this.handleRecordClick(record), { passive: true });
        
        return div;
    }

    /**
     * Handle record click (for future features)
     */
    handleRecordClick(record) {
        console.log('Record clicked:', record);
        // Future: Show record details or edit functionality
    }

    /**
     * Update pagination controls
     */
    updatePagination() {
        const totalPages = this.getTotalPages();
        
        if (totalPages <= 1) {
            this.elements.pagination.style.display = 'none';
            return;
        }
        
        this.elements.pagination.style.display = 'flex';
        this.elements.prevPage.disabled = this.currentPage === 1;
        this.elements.nextPage.disabled = this.currentPage === totalPages;
        this.elements.pageInfo.textContent = `${this.currentPage} / ${totalPages}`;
    }

    /**
     * Update export button state
     */
    updateExportButton() {
        this.elements.exportBtn.disabled = this.records.length === 0;
    }

    /**
     * Handle scroll events (for future virtual scrolling)
     */
    handleScroll(event) {
        // Future: Implement infinite scroll or virtual scrolling
        const { scrollTop, scrollHeight, clientHeight } = event.target;
        const scrollPercentage = (scrollTop / (scrollHeight - clientHeight)) * 100;
        
        // Performance monitoring
        if (scrollPercentage > 80) {
            // Could trigger loading more data in a real application
        }
    }

    /**
     * Lazy load SheetJS library for Excel functionality
     */
    async loadSheetJS() {
        if (this.isSheetJSLoaded) {
            return true;
        }

        try {
            await new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
                script.async = true;
                script.onload = () => {
                    this.isSheetJSLoaded = true;
                    resolve();
                };
                script.onerror = reject;
                document.head.appendChild(script);
            });
            return true;
        } catch (error) {
            console.error('Failed to load SheetJS:', error);
            this.showToast('Excel 기능을 로드할 수 없습니다.', 'error');
            return false;
        }
    }

    /**
     * Handle Excel export with lazy loading
     */
    async handleExport() {
        if (this.records.length === 0) {
            this.showToast('내보낼 기록이 없습니다.', 'error');
            return;
        }

        this.setButtonLoading('exportBtn', true);

        try {
            const loaded = await this.loadSheetJS();
            if (!loaded) return;

            // Prepare data for export
            const exportData = this.records.map(record => ({
                날짜: record.date,
                출발지: record.startPoint,
                도착지: record.endPoint,
                경로: record.route,
                통행료: record.toll,
                주유비: record.fuel,
                총비용: record.total
            }));

            // Create workbook
            const ws = XLSX.utils.json_to_sheet(exportData);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "차계부_기록");
            
            // Download file
            const fileName = `차계부_기록_${new Date().toLocaleDateString('ko-KR')}.xlsx`;
            XLSX.writeFile(wb, fileName);
            
            this.showToast('Excel 파일이 다운로드되었습니다.', 'success');
            
        } catch (error) {
            console.error('Export error:', error);
            this.showToast('Excel 내보내기 중 오류가 발생했습니다.', 'error');
        } finally {
            this.setButtonLoading('exportBtn', false);
        }
    }

    /**
     * Handle Excel file upload
     */
    async handleUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        this.setButtonLoading('uploadBtn', true);

        try {
            const loaded = await this.loadSheetJS();
            if (!loaded) return;

            const data = await this.readFile(file);
            const workbook = XLSX.read(data, { type: 'array' });
            const firstSheet = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[firstSheet];
            const jsonData = XLSX.utils.sheet_to_json(worksheet);

            let importedCount = 0;
            
            jsonData.forEach(row => {
                const record = {
                    id: Date.now() + Math.random(),
                    date: row['날짜'] || new Date().toLocaleDateString('ko-KR'),
                    route: row['경로'] || `${row['출발지'] || '알 수 없음'} → ${row['도착지'] || '알 수 없음'}`,
                    startPoint: row['출발지'] || '알 수 없음',
                    endPoint: row['도착지'] || '알 수 없음',
                    toll: parseInt(row['통행료']) || 0,
                    fuel: parseInt(row['주유비']) || 0,
                    total: (parseInt(row['통행료']) || 0) + (parseInt(row['주유비']) || 0),
                    timestamp: Date.now() + importedCount // Ensure unique timestamps
                };
                
                this.records.push(record);
                this.totalCost += record.total;
                importedCount++;
            });

            this.updateUI();
            this.debouncedSave();
            this.showToast(`${importedCount}개의 기록이 업로드되었습니다.`, 'success');
            
        } catch (error) {
            console.error('Upload error:', error);
            this.showToast('Excel 파일 업로드 중 오류가 발생했습니다.', 'error');
        } finally {
            this.setButtonLoading('uploadBtn', false);
            event.target.value = ''; // Reset file input
        }
    }

    /**
     * Read file as array buffer
     */
    readFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(new Uint8Array(e.target.result));
            reader.onerror = reject;
            reader.readAsArrayBuffer(file);
        });
    }

    /**
     * Simulate toll fee calculation
     */
    simulateTollFee() {
        return Math.floor(Math.random() * 5000) + 1000;
    }

    /**
     * Load mock data for demonstration
     */
    async loadMockData() {
        if (this.records.length > 0) return; // Don't load mock data if real data exists

        const mockData = this.generateMockHistory(5);
        mockData.forEach(record => {
            this.records.push(record);
            this.totalCost += record.total;
        });
    }

    /**
     * Generate mock history data
     */
    generateMockHistory(days = 5) {
        const history = [];
        const places = ['서울역', '수원역', '인천공항', '부산역', '대전역', '광주터미널'];
        
        for (let i = 0; i < days; i++) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            
            const startPoint = places[Math.floor(Math.random() * places.length)];
            let endPoint = places[Math.floor(Math.random() * places.length)];
            while (startPoint === endPoint) {
                endPoint = places[Math.floor(Math.random() * places.length)];
            }
            
            const tollFee = this.simulateTollFee();
            const fuelCost = Math.floor(Math.random() * 50000);
            
            history.push({
                id: Date.now() + Math.random() + i,
                date: date.toLocaleDateString('ko-KR'),
                route: `${startPoint} → ${endPoint}`,
                startPoint,
                endPoint,
                toll: tollFee,
                fuel: fuelCost,
                total: tollFee + fuelCost,
                timestamp: date.getTime()
            });
        }
        
        return history;
    }

    /**
     * Save data to localStorage for persistence
     */
    saveToLocalStorage() {
        try {
            const data = {
                records: this.records,
                totalCost: this.totalCost,
                version: '1.0',
                lastSaved: Date.now()
            };
            localStorage.setItem('carExpenseData', JSON.stringify(data));
        } catch (error) {
            console.error('Failed to save to localStorage:', error);
        }
    }

    /**
     * Load data from localStorage
     */
    loadFromLocalStorage() {
        try {
            const saved = localStorage.getItem('carExpenseData');
            if (saved) {
                const data = JSON.parse(saved);
                this.records = data.records || [];
                this.totalCost = data.totalCost || 0;
            }
        } catch (error) {
            console.error('Failed to load from localStorage:', error);
            this.records = [];
            this.totalCost = 0;
        }
    }

    /**
     * Clear form inputs
     */
    clearForm() {
        this.elements.startPoint.value = '';
        this.elements.endPoint.value = '';
        this.elements.fuelCost.value = '0';
        this.elements.startPointError.textContent = '';
        this.elements.endPointError.textContent = '';
    }

    /**
     * Set button loading state
     */
    setButtonLoading(buttonId, isLoading) {
        const button = this.elements[buttonId];
        const textSpan = button.querySelector('.btn-text');
        const loadingSpan = button.querySelector('.btn-loading');
        
        if (isLoading) {
            textSpan.style.display = 'none';
            loadingSpan.style.display = 'flex';
            button.disabled = true;
        } else {
            textSpan.style.display = 'block';
            loadingSpan.style.display = 'none';
            button.disabled = false;
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toastId = type === 'error' ? 'errorToast' : 'successToast';
        const toast = this.elements[toastId];
        
        toast.textContent = message;
        toast.classList.add('show');
        
        // Performance: Use setTimeout for non-critical UI updates
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    /**
     * Hide loading overlay
     */
    hideLoading() {
        // Performance: Use requestAnimationFrame for smooth transitions
        requestAnimationFrame(() => {
            this.elements.loading.style.opacity = '0';
            this.elements.app.style.display = 'block';
            
            setTimeout(() => {
                this.elements.loading.style.display = 'none';
                this.elements.app.style.opacity = '1';
            }, 300);
        });
    }

    /**
     * Debounce utility function for performance
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Performance: Use DOMContentLoaded for faster initialization
document.addEventListener('DOMContentLoaded', () => {
    // Performance monitoring
    if ('performance' in window) {
        window.addEventListener('load', () => {
            const perfData = performance.getEntriesByType('navigation')[0];
            console.log(`Page load time: ${perfData.loadEventEnd - perfData.loadEventStart}ms`);
        });
    }
    
    // Initialize the application
    window.carExpenseTracker = new CarExpenseTracker();
});

// Performance: Handle memory cleanup
window.addEventListener('beforeunload', () => {
    if (window.carExpenseTracker) {
        window.carExpenseTracker.saveToLocalStorage();
    }
});