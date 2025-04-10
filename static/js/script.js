        // JavaScript untuk progress, preview, dan lainnya
        function updateQualityOptions() {
            const format = document.querySelector('select[name="format"]').value;
            const qualitySelect = document.getElementById('qualitySelect');
            if (format === 'mp3') {
                qualitySelect.innerHTML = `
                    <option value="192">192 kbps (Good Quality)</option>
                    <option value="320">320 kbps (Best Quality)</option>
                `;
            } else {
                qualitySelect.innerHTML = `
                    <option value="360">360p</option>
                    <option value="720">720p (HD)</option>
                    <option value="1080">1080p (Full HD)</option>
                `;
            }
        }

        function startConversion() {
            const btn = document.getElementById('convertBtn');
            btn.disabled = true;
            btn.textContent = "Converting...";
            
            document.getElementById('progressContainer').style.display = 'block';
            checkProgress();
        }

        function checkProgress() {
            fetch('/progress')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('progressFill').style.width = data.progress + '%';
                    document.getElementById('progressPercent').textContent = data.progress.toFixed(1) + '%';
                    document.getElementById('progressSpeed').textContent = 'Speed: ' + data.speed;
                    document.getElementById('progressETA').textContent = 'ETA: ' + data.eta;
                    
                    if (data.progress < 100) {
                        setTimeout(checkProgress, 1000);
                    } else {
                        document.getElementById('convertBtn').disabled = false;
                        document.getElementById('convertBtn').textContent = "Convert";
                        const downloadLink = document.getElementById('downloadLink');
                        if (downloadLink) {
                            // Auto-click and hide after short delay
                            setTimeout(() => {
                                downloadLink.click();
                                const downloadSection = document.querySelector('.download-link');
                                if (downloadSection) downloadSection.style.display = "none";
                            }, 1000);
                        }
                    }
                });
        }

        document.addEventListener("DOMContentLoaded", () => {
            const downloadLink = document.getElementById('downloadLink');
            if (downloadLink) {
                downloadLink.addEventListener('click', () => {
                    const downloadSection = document.querySelector('.download-link');
                    if (downloadSection) downloadSection.style.display = "none";

                    // Show animated toast
                    showToast("✅ File berhasil diunduh dan sudah dihapus dari server.");
                });
            }
        });

        function showToast(message) {
            const toast = document.createElement('div');
            toast.classList.add('toast');
            toast.textContent = message;
            document.body.appendChild(toast);

            // Trigger animation
            setTimeout(() => toast.classList.add('show'), 100);

            // Remove after 3 seconds
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 500);
            }, 3000);
        }

        function toggleTheme() {
            const isDark = document.body.classList.toggle('dark');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        }

        window.addEventListener('DOMContentLoaded', () => {
            if (localStorage.getItem('theme') === 'dark') {
            document.body.classList.add('dark');
            document.getElementById('themeToggle').checked = true;
            }
        });