// Field Diagnostic System - Client-side Logic

// Typing animation
const typingTitle = document.getElementById('typingTitle');
const titleText = 'Intelligent Equipment Diagnostics';
let charIndex = 0;

function typeText() {
    if (charIndex < titleText.length) {
        typingTitle.textContent += titleText.charAt(charIndex);
        charIndex++;
        setTimeout(typeText, 50);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    setTimeout(typeText, 300);
});

// Modal functionality
const aboutModal = document.getElementById('aboutModal');
const closeModal = document.getElementById('closeModal');
const aboutLinks = document.querySelectorAll('a[href="#"]');

aboutLinks.forEach(link => {
    if (link.textContent.includes('About')) {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            aboutModal.classList.add('active');
        });
    }
});

closeModal.addEventListener('click', () => {
    aboutModal.classList.remove('active');
});

aboutModal.addEventListener('click', (e) => {
    if (e.target === aboutModal) {
        aboutModal.classList.remove('active');
    }
});

// Form handling
const form = document.getElementById('diagnoseForm');
const resultCard = document.getElementById('resultCard');
const result = document.getElementById('result');
const submitBtn = document.getElementById('submitBtn');
const btnText = document.getElementById('btnText');

function normalizeDiagnosis(data) {
    if (!data || typeof data !== 'object') return {};
    
    let normalized = { ...data };
    if (data.final_diagnosis && typeof data.final_diagnosis === 'object') {
        Object.assign(normalized, data.final_diagnosis);
    }
    if (data.repair_plan && typeof data.repair_plan === 'object') {
        Object.assign(normalized, data.repair_plan);
    }
    if (data.escalation_ticket && typeof data.escalation_ticket === 'object') {
        Object.assign(normalized, data.escalation_ticket);
    }

    if (normalized.inventory && typeof normalized.inventory === 'object') {
        if (!Array.isArray(normalized.inventory) && normalized.inventory.part) {
            normalized.inventory = {
                [normalized.inventory.part]: normalized.inventory.available
            };
        } else if (Array.isArray(normalized.inventory)) {
            let inventoryMap = {};
            normalized.inventory.forEach(item => {
                if (item?.part && item.available !== undefined) {
                    inventoryMap[item.part] = item.available;
                }
            });
            if (Object.keys(inventoryMap).length > 0) {
                normalized.inventory = inventoryMap;
            }
        }
    }
    return normalized;
}

function applyStyles(element, styles) {
    Object.entries(styles).forEach(([property, value]) => {
        if (value !== undefined && value !== null) {
            element.style[property] = value;
        }
    });
}

function createTextElement(tagName, text, styles = {}, className = '') {
    const element = document.createElement(tagName);
    if (className) {
        element.className = className;
    }
    if (text !== undefined && text !== null) {
        element.textContent = String(text);
    }
    applyStyles(element, styles);
    return element;
}

function createSafeList(items, listTag, itemTag, itemStyles = {}, className = '') {
    const list = document.createElement(listTag);
    if (className) {
        list.className = className;
    }
    items.forEach(item => {
        const listItem = document.createElement(itemTag);
        applyStyles(listItem, itemStyles);
        listItem.textContent = String(item);
        list.appendChild(listItem);
    });
    return list;
}

function renderDiagnosis(data) {
    const root = document.createElement('div');

    if (!data || typeof data !== 'object') {
        const warningBox = createTextElement('div', '⚠ No Diagnosis Data', {
            background: 'rgba(245,158,11,0.1)',
            border: '2px solid var(--warning)',
            borderRadius: '12px',
            padding: '1.5rem',
            textAlign: 'center'
        });
        const warningTitle = createTextElement('div', '⚠ No Diagnosis Data', {
            fontSize: '1.2rem',
            color: 'var(--warning)',
            fontWeight: '700',
            marginBottom: '0.5rem'
        });
        const warningMessage = createTextElement('p', 'The diagnostic system did not return structured results.', {
            color: '#666'
        });
        warningBox.appendChild(warningTitle);
        warningBox.appendChild(warningMessage);
        root.appendChild(warningBox);
        return root;
    }

    const info = normalizeDiagnosis(data);
    const readyToProceed = info.proceed !== false;
    const needsEscalation = info.escalation_needed === true;
    const needsFollowUp = info.needs_follow_up === true;

    if (readyToProceed && !needsEscalation) {
        const banner = createTextElement('div', '', {
            background: 'rgba(38,196,133,0.1)',
            border: '2px solid var(--success)',
            borderRadius: '12px',
            padding: '1.25rem',
            marginBottom: '1.5rem',
            textAlign: 'center'
        });
        const title = createTextElement('div', '✓ Ready to Proceed', {
            fontSize: '1.2rem',
            color: 'var(--success)',
            fontWeight: '700'
        });
        const subtitle = createTextElement('div', 'All parts available. Begin repairs immediately.', {
            color: '#666',
            fontSize: '0.9rem'
        });
        banner.appendChild(title);
        banner.appendChild(subtitle);
        root.appendChild(banner);
    } else if (needsFollowUp && !needsEscalation) {
        const banner = createTextElement('div', '', {
            background: 'rgba(245,158,11,0.1)',
            border: '2px solid var(--warning)',
            borderRadius: '12px',
            padding: '1.25rem',
            marginBottom: '1.5rem',
            textAlign: 'center'
        });
        const title = createTextElement('div', '⚠ More Information Needed', {
            fontSize: '1.2rem',
            color: 'var(--warning)',
            fontWeight: '700'
        });
        const subtitle = createTextElement('div', 'Answer the follow-up checks below to improve diagnosis confidence.', {
            color: '#666',
            fontSize: '0.9rem'
        });
        banner.appendChild(title);
        banner.appendChild(subtitle);
        root.appendChild(banner);
    } else if (needsEscalation) {
        const banner = createTextElement('div', '', {
            background: 'rgba(239,68,68,0.1)',
            border: '2px solid var(--error)',
            borderRadius: '12px',
            padding: '1.25rem',
            marginBottom: '1.5rem',
            textAlign: 'center'
        });
        const title = createTextElement('div', '⚠ Escalation Required', {
            fontSize: '1.2rem',
            color: 'var(--error)',
            fontWeight: '700'
        });
        const subtitle = createTextElement('div', 'Parts unavailable or additional review needed.', {
            color: '#666',
            fontSize: '0.9rem'
        });
        banner.appendChild(title);
        banner.appendChild(subtitle);
        root.appendChild(banner);
    }

    const issueCard = createTextElement('div', '', {
        background: 'linear-gradient(135deg, rgba(255,245,240,0.6) 0%, rgba(240,250,255,0.5) 100%)',
        borderRadius: '12px',
        padding: '1.25rem',
        marginBottom: '1.5rem',
        border: '1px solid rgba(255,107,91,0.15)'
    });
    const issueHeaderRow = document.createElement('div');
    issueHeaderRow.style.display = 'flex';
    issueHeaderRow.style.justifyContent = 'space-between';
    issueHeaderRow.style.alignItems = 'start';

    const issueBody = document.createElement('div');
    issueBody.style.flex = '1';

    const issueTitle = createTextElement('h3', 'ISSUE', {
        color: 'var(--dark)',
        fontSize: '0.9rem',
        marginBottom: '0.5rem',
        fontWeight: '700'
    });
    const issueText = createTextElement('p', info.root_cause || 'Analysis in progress', {
        color: '#555',
        fontSize: '1rem',
        lineHeight: '1.4'
    });

    issueBody.appendChild(issueTitle);
    issueBody.appendChild(issueText);
    issueHeaderRow.appendChild(issueBody);

    if (info.confidence) {
        const percentage = Math.round(info.confidence * 100);
        let color = 'var(--success)';
        if (percentage < 60) color = 'var(--error)';
        else if (percentage < 80) color = 'var(--warning)';

        const confidenceBox = document.createElement('div');
        confidenceBox.style.textAlign = 'center';
        confidenceBox.style.paddingLeft = '1.5rem';

        const confidenceLabel = createTextElement('div', 'Confidence', {
            fontSize: '0.75rem',
            color: '#999',
            marginBottom: '0.25rem',
            textTransform: 'uppercase',
            fontWeight: '600'
        });
        const confidenceValue = createTextElement('div', `${percentage}%`, {
            fontSize: '1.8rem',
            fontWeight: '700',
            color
        });

        confidenceBox.appendChild(confidenceLabel);
        confidenceBox.appendChild(confidenceValue);
        issueHeaderRow.appendChild(confidenceBox);
    }

    issueCard.appendChild(issueHeaderRow);
    root.appendChild(issueCard);

    if (info.required_parts && info.required_parts.length > 0) {
        const partsCard = createTextElement('div', '', {
            background: 'transparent',
            borderRadius: '12px',
            padding: '0.5rem 0',
            marginBottom: '1.5rem'
        });
        partsCard.appendChild(createTextElement('h3', 'PARTS NEEDED', {
            color: 'var(--dark)',
            fontSize: '0.9rem',
            marginBottom: '0.75rem',
            fontWeight: '700'
        }));

        const inventoryGrid = document.createElement('div');
        let allInStock = true;

        for (const [partName, quantity] of Object.entries(info.inventory || {})) {
            const inStock = quantity > 0;
            if (!inStock) allInStock = false;
            const stockColor = inStock ? 'var(--success)' : 'var(--error)';
            const bgColor = inStock ? 'rgba(38,196,133,0.1)' : 'rgba(239,68,68,0.1)';
            const stockStatus = inStock ? '✓ IN STOCK' : '✗ OUT';

            const item = createTextElement('div', '', {
                background: bgColor,
                border: `1px solid ${stockColor}`
            }, 'inventory-item');
            item.appendChild(createTextElement('div', String(partName), {}, 'inventory-item-name'));
            item.appendChild(createTextElement('div', String(quantity), {
                color: stockColor
            }, 'inventory-item-count'));
            item.appendChild(createTextElement('div', stockStatus, {
                fontSize: '0.65rem',
                color: stockColor,
                fontWeight: '700'
            }));
            inventoryGrid.appendChild(item);
        }

        partsCard.appendChild(inventoryGrid);
        if (!allInStock) {
            const stockWarning = createTextElement('div', '⚠ Out of Stock: Escalation ticket created below.', {
                background: 'rgba(239,68,68,0.1)',
                borderLeft: '4px solid var(--error)',
                padding: '0.75rem',
                borderRadius: '4px',
                color: '#C00',
                fontSize: '0.85rem'
            });
            partsCard.appendChild(stockWarning);
        }
        root.appendChild(partsCard);
    }

    if (info.steps && info.steps.length > 0) {
        const stepsCard = createTextElement('div', '', {
            background: 'linear-gradient(135deg, rgba(255,245,240,0.6) 0%, rgba(240,250,255,0.5) 100%)',
            borderRadius: '12px',
            padding: '1.25rem',
            marginBottom: '1.5rem',
            border: '1px solid rgba(75,184,217,0.15)'
        });
        stepsCard.appendChild(createTextElement('h3', 'REPAIR STEPS', {
            color: 'var(--dark)',
            fontSize: '0.9rem',
            marginBottom: '1rem',
            fontWeight: '700'
        }));

        const orderedList = document.createElement('ol');
        orderedList.style.color = '#555';
        orderedList.style.lineHeight = '1.7';
        orderedList.style.paddingLeft = '1.5rem';
        orderedList.style.fontSize = '0.95rem';

        info.steps.slice(0, 4).forEach(step => {
            const listItem = document.createElement('li');
            listItem.style.marginBottom = '0.5rem';
            listItem.textContent = String(step);
            orderedList.appendChild(listItem);
        });

        stepsCard.appendChild(orderedList);
        root.appendChild(stepsCard);
    }

    if (Array.isArray(info.missing_parts) && info.missing_parts.length > 0) {
        const missingPartsCard = createTextElement('div', '', {
            background: 'rgba(239,68,68,0.1)',
            border: '2px solid var(--error)',
            borderRadius: '12px',
            padding: '1.25rem',
            marginBottom: '1.5rem'
        });
        missingPartsCard.appendChild(createTextElement('h3', 'MISSING PARTS', {
            color: 'var(--error)',
            fontSize: '0.9rem',
            marginBottom: '0.75rem',
            fontWeight: '700'
        }));
        missingPartsCard.appendChild(createSafeList(info.missing_parts, 'ul', 'li', {
            color: '#8a2020',
            lineHeight: '1.6',
            paddingLeft: '1.2rem',
            fontSize: '0.9rem'
        }));
        root.appendChild(missingPartsCard);
    }

    if (Array.isArray(info.follow_ups) && info.follow_ups.length > 0) {
        const followUpCard = createTextElement('div', '', {
            background: 'rgba(245,158,11,0.1)',
            border: '2px solid var(--warning)',
            borderRadius: '12px',
            padding: '1.25rem',
            marginBottom: '1.5rem'
        });
        followUpCard.appendChild(createTextElement('h3', 'FOLLOW-UP CHECKS', {
            color: '#8B5E00',
            fontSize: '0.9rem',
            marginBottom: '0.75rem',
            fontWeight: '700'
        }));
        followUpCard.appendChild(createSafeList(info.follow_ups, 'ol', 'li', {
            marginBottom: '0.45rem',
            color: '#7a5a00',
            lineHeight: '1.65',
            paddingLeft: '1.2rem',
            fontSize: '0.9rem'
        }));
        root.appendChild(followUpCard);
    }

    if (needsEscalation) {
        const escalationCard = createTextElement('div', '', {
            background: 'rgba(239,68,68,0.1)',
            border: '2px solid var(--error)',
            borderRadius: '12px',
            padding: '1.25rem'
        });
        escalationCard.appendChild(createTextElement('h3', '🎫 ESCALATION TICKET', {
            color: 'var(--error)',
            fontSize: '0.9rem',
            marginBottom: '1rem',
            fontWeight: '700'
        }));

        const ticketGrid = document.createElement('div');
        ticketGrid.style.display = 'grid';
        ticketGrid.style.gridTemplateColumns = '1fr 1fr';
        ticketGrid.style.gap = '1rem';

        const ticketId = document.createElement('div');
        const ticketIdLabel = createTextElement('div', 'Ticket ID', {
            fontSize: '0.75rem',
            color: '#999',
            marginBottom: '0.3rem',
            textTransform: 'uppercase',
            fontWeight: '600'
        });
        const ticketNumber = createTextElement('div', info.ticket?.ticket_id || 'TKT-' + Math.random().toString(36).substr(2, 9).toUpperCase(), {
            fontSize: '1rem',
            color: 'var(--dark)',
            fontWeight: '700',
            fontFamily: 'monospace'
        });
        ticketId.appendChild(ticketIdLabel);
        ticketId.appendChild(ticketNumber);

        const ticketPriority = document.createElement('div');
        const priorityLabel = createTextElement('div', 'Priority', {
            fontSize: '0.75rem',
            color: '#999',
            marginBottom: '0.3rem',
            textTransform: 'uppercase',
            fontWeight: '600'
        });
        const priorityValue = createTextElement('div', info.ticket?.priority || 'HIGH', {
            fontSize: '1rem',
            color: 'var(--error)',
            fontWeight: '700'
        });
        ticketPriority.appendChild(priorityLabel);
        ticketPriority.appendChild(priorityValue);

        ticketGrid.appendChild(ticketId);
        ticketGrid.appendChild(ticketPriority);
        escalationCard.appendChild(ticketGrid);

        if (info.reason) {
            const reasonBlock = createTextElement('div', `Reason: ${info.reason}`, {
                marginTop: '1rem',
                padding: '0.75rem',
                background: 'linear-gradient(135deg, rgba(255,245,240,0.4) 0%, rgba(240,250,255,0.3) 100%)',
                borderRadius: '6px',
                color: '#555',
                fontSize: '0.85rem',
                borderLeft: '3px solid rgba(255,107,91,0.3)'
            });
            escalationCard.appendChild(reasonBlock);
        }

        root.appendChild(escalationCard);
    }

    if (info.notes) {
        const notesBlock = createTextElement('div', `📌 ${info.notes}`, {
            background: 'rgba(255,217,61,0.1)',
            borderLeft: '4px solid var(--accent)',
            padding: '1rem',
            borderRadius: '8px',
            color: '#8B5E00',
            fontSize: '0.85rem',
            lineHeight: '1.5',
            marginTop: '1rem'
        });
        root.appendChild(notesBlock);
    }

    return root;
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    submitBtn.disabled = true;

    btnText.replaceChildren();
    const spinner = document.createElement('span');
    spinner.className = 'spinner';
    btnText.appendChild(spinner);
    btnText.appendChild(document.createTextNode('Analyzing...'));

    resultCard.classList.remove('hidden');
    result.replaceChildren();

    const loadingText = document.createElement('p');
    loadingText.style.color = '#888';
    loadingText.textContent = 'Running diagnostic agents...';
    result.appendChild(loadingText);

    const deviceId = document.getElementById('device').value;
    const errorCode = document.getElementById('error_code').value;
    const problemDescription = document.getElementById('description').value;

    try {
        const response = await fetch('/diagnose', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device: deviceId,
                error_code: errorCode,
                description: problemDescription
            })
        });

        const responseData = await response.json();

        if (response.ok) {
            result.className = 'result success';
            let diagnosisResult = responseData.result?.final_response || responseData.result || responseData;

            if (typeof diagnosisResult === 'string') {
                try {
                    diagnosisResult = JSON.parse(diagnosisResult);
                } catch (e) {
                    result.replaceChildren();
                    const safeText = document.createElement('p');
                    safeText.style.color = '#666';
                    safeText.textContent = diagnosisResult;
                    result.appendChild(safeText);
                    submitBtn.disabled = false;
                    btnText.replaceChildren(document.createTextNode('Run Diagnosis'));
                    return;
                }
            }

            result.replaceChildren(renderDiagnosis(diagnosisResult));
        } else {
            result.className = 'result error';
            result.replaceChildren();
            const errorPre = document.createElement('pre');
            errorPre.textContent = JSON.stringify(responseData, null, 2);
            result.appendChild(errorPre);
        }
    } catch (err) {
        result.className = 'result error';
        result.replaceChildren();

        const errorCard = document.createElement('div');
        errorCard.style.background = 'rgba(239,68,68,0.1)';
        errorCard.style.border = '2px solid var(--error)';
        errorCard.style.borderRadius = '12px';
        errorCard.style.padding = '1.5rem';

        const errorTitle = createTextElement('h3', '⚠ Error', {
            color: 'var(--error)',
            marginBottom: '1rem'
        });
        const errorMessage = createTextElement('p', err.message || 'An unexpected error occurred', {
            color: '#666',
            fontFamily: 'monospace'
        });
        const errorHint = createTextElement('p', 'Please check the console for more details.', {
            color: '#999',
            fontSize: '0.85rem',
            marginTop: '0.5rem'
        });

        errorCard.appendChild(errorTitle);
        errorCard.appendChild(errorMessage);
        errorCard.appendChild(errorHint);
        result.appendChild(errorCard);
        console.error('Diagnostic error:', err);
    }

    submitBtn.disabled = false;
    btnText.replaceChildren(document.createTextNode('Run Diagnosis'));
});
