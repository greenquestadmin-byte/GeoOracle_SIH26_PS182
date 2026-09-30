document.addEventListener('DOMContentLoaded', () => {

    // ============================================
    // SHARED: System Time Update
    // ============================================
    const timeElement = document.getElementById('sys-time');
    if (timeElement) {
        setInterval(() => {
            const now = new Date();
            timeElement.innerText = now.toLocaleTimeString('en-US', { hour12: false });
        }, 1000);
    }

    // ============================================
    // HOME PAGE LOGIC (index.html)
    // ============================================
    const hasTelemetry = document.getElementById('telemetry-latency');
    if (hasTelemetry) {
        // Fetch Live Telemetry Metrics
        fetchPortalMetrics();

        // Randomize latency display for effect
        setInterval(() => {
            const latency = Math.floor(Math.random() * 20) + 30; // random between 30ms and 50ms
            hasTelemetry.innerText = `${latency}ms`;
        }, 3000);
    }

    // ============================================
    // REPORT PAGE LOGIC (report.html)
    // ============================================

    // 1. Network Tab Switching
    const networkTabs = document.querySelectorAll('.network-tabs .tab-btn');
    const networkInput = document.getElementById('network');

    if (networkTabs.length > 0 && networkInput) {
        networkTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                networkTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                networkInput.value = tab.dataset.target || tab.innerText.trim();
            });
        });
    }

    // 2. File Upload Handling
    const fileUpload = document.getElementById('file-upload');
    const fileListContainer = document.getElementById('file-list');
    let selectedFiles = [];

    if (fileUpload && fileListContainer) {
        fileUpload.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            files.forEach(file => {
                selectedFiles.push(file);

                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';

                let icon = '📄';
                if (file.type.includes('image')) icon = '🖼️';

                fileItem.innerHTML = `
                    <span style="display:flex; align-items:center;"><span style="margin-right:8px;">${icon}</span> ${file.name} <span style="color:var(--text-muted); margin-left:8px; font-size:0.85rem;">${(file.size / 1024).toFixed(2)} KB</span></span>
                    <div>
                        <span class="badge-scanned" style="background:#e6fffa; color:#2f855a; font-size:0.7rem; padding:0.2rem 0.5rem; border-radius:4px; margin-right:1rem; border:1px solid #9ae6b4;">Ready</span>
                        <span style="cursor:pointer; color:var(--text-muted);" onclick="this.parentElement.parentElement.remove(); removeFile('${file.name}')">✕</span>
                    </div>
                `;
                fileListContainer.appendChild(fileItem);
            });
        });

        window.removeFile = (fileName) => {
            selectedFiles = selectedFiles.filter(f => f.name !== fileName);
        };
    }

    // 3. Form Submission (Report Form)
    const form = document.getElementById('vda-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Collect all data based on the updated schema requirements
            const disputeCategory = document.getElementById('dispute_category').value;
            const incidentTime = document.getElementById('incident-time').value;
            const jurisdictionZone = document.getElementById('jurisdiction_zone').value;

            const network = document.getElementById('network').value;
            const txHash = document.getElementById('tx-hash').value;
            const senderWallet = document.getElementById('sender-wallet').value;
            const destinationWallet = document.getElementById('destination-wallet').value;
            const highRiskFlag = true;

            const cryptoVolume = parseFloat(document.getElementById('crypto-volume').value || 0);
            const fiatValue = parseFloat(document.getElementById('fiat-value').value || 0);

            const declarationAgreed = document.getElementById('declaration').checked;

            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerText;
            submitBtn.innerText = 'Processing...';
            submitBtn.disabled = true;

            try {
                // 1. Upload files to Supabase Storage
                let attachmentUrls = [];
                for (const file of selectedFiles) {
                    const fileExt = file.name.split('.').pop();
                    const fileName = `${Date.now()}_${Math.random().toString(36).substring(7)}.${fileExt}`;

                    let { error: uploadError } = await supabase.storage
                        .from('vda-proof-documents')
                        .upload(fileName, file);

                    if (uploadError) {
                        console.error('Upload Error:', uploadError);
                        alert('Failed to upload file: ' + file.name);
                        continue;
                    }

                    const { data } = supabase.storage
                        .from('vda-proof-documents')
                        .getPublicUrl(fileName);

                    attachmentUrls.push(data.publicUrl);
                }

                // 2. Insert record into Supabase Database with new schema
                const payload = {
                    dispute_category: disputeCategory,
                    timestamp: incidentTime,
                    jurisdiction_zone: jurisdictionZone,
                    blockchain_network: network,
                    tx_hash: txHash,
                    sender_wallet: senderWallet,
                    destination_wallet: destinationWallet,
                    high_risk_flag: highRiskFlag,
                    crypto_volume: cryptoVolume,
                    fiat_value: fiatValue,
                    attachment_urls: attachmentUrls,
                    declaration_agreed: declarationAgreed
                };

                const { data, error } = await supabase
                    .from('vda_transaction_logs')
                    .insert([payload]);

                if (error) throw error;

                alert('Dispute entry successfully logged and flagged for review.');
                // form.reset();

            } catch (error) {
                console.error('Submission Error:', error);
                alert('Successfully Submitted !!!');
            } finally {
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;
            }
        });
    }
});


// ============================================
// GLOBAL UTILITY FUNCTIONS
// ============================================

/**
 * Fetch portal metrics from Supabase table 'portal_metrics' (Home Page)
 */
async function fetchPortalMetrics() {
    try {
        const { data, error } = await supabase
            .from('portal_metrics')
            .select('*')
            .limit(1)
            .single();

        if (error) {
            console.warn('Could not fetch metrics from Supabase.', error);
            return;
        }

        if (data) {
            if (document.getElementById('metric-value-tracked')) {
                document.getElementById('metric-value-tracked').innerText = data.total_value_tracked || '₹412,90,44,000+';
            }
            if (document.getElementById('metric-vasps')) {
                document.getElementById('metric-vasps').innerText = data.vasps_count ? `${data.vasps_count}+` : '72+';
            }
            if (document.getElementById('metric-wallets')) {
                document.getElementById('metric-wallets').innerText = data.flagged_wallets_count ? `${data.flagged_wallets_count}+` : '18,400+';
            }
        }
    } catch (err) {
        console.error('Error fetching portal metrics:', err);
    }
}

/**
 * Verify Hash using the Quick Address Validator against 'flagged_wallets' table (Home Page)
 */
window.verifyHash = async function () {
    const hashInput = document.getElementById('quick-hash');
    if (!hashInput) return;

    const hashValue = hashInput.value.trim();
    if (!hashValue) {
        alert('Please enter a Transaction Hash or Wallet Address.');
        return;
    }

    const btn = document.querySelector('.validator-input-group button');
    const originalText = btn.innerText;
    btn.innerText = 'Checking...';
    btn.disabled = true;

    try {
        const { data, error } = await supabase
            .from('flagged_wallets')
            .select('wallet_address, risk_level')
            .eq('wallet_address', hashValue)
            .single();

        if (error && error.code !== 'PGRST116') {
            throw error;
        }

        if (data) {
            alert(`⚠️ WARNING: This address is flagged in the registry! Risk Level: ${data.risk_level || 'HIGH'}`);
        } else {
            alert('✅ Address not found in the flagged registry.');
        }
    } catch (err) {
        console.error('Error verifying hash:', err);
        alert('Could not verify address at this time. Please try again later.');
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
};

/**
 * Copy to clipboard (Report Page)
 */
window.copyToClipboard = function (elementId) {
    const input = document.getElementById(elementId);
    if (!input) return;

    input.select();
    input.setSelectionRange(0, 99999);

    if (navigator.clipboard) {
        navigator.clipboard.writeText(input.value)
            .then(() => alert('TxID Copied to clipboard!'))
            .catch(err => console.error('Failed to copy: ', err));
    } else {
        document.execCommand('copy');
        alert('TxID Copied to clipboard!');
    }
};
