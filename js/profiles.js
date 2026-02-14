// Profile Management Functions
async function loadProfiles() {
    try {
        document.getElementById('loadingArea').style.display = 'block';
        document.getElementById('profilesGrid').style.display = 'none';
        
        currentProfiles = await datingDB.getProfilesByFilter(currentFilter);
        displayProfiles(currentProfiles);
        
    } catch (error) {
        console.error('Error loading profiles:', error);
        updateStatus('Error loading profiles: ' + error.message);
    } finally {
        document.getElementById('loadingArea').style.display = 'none';
        document.getElementById('profilesGrid').style.display = 'grid';
    }
}

function displayProfiles(profiles) {
    const grid = document.getElementById('profilesGrid');
    grid.innerHTML = '';

    profiles.forEach(profile => {
        const card = createProfileCard(profile);
        grid.appendChild(card);
    });

    if (profiles.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #666;">No profiles found for current filter.</div>';
    }
}

function createProfileCard(profile) {
    const card = document.createElement('div');
    card.className = 'profile-card';
    card.onclick = () => showProfileModal(profile);
    
    card.innerHTML = `
        <div class="profile-image">
            ${profile.avatar || '👤'}
            <div class="ai-match">${profile.aiCompatibility}% Match</div>
        </div>
        <div class="profile-info">
            <div class="profile-basics">
                <div class="name-age">${profile.name}, ${profile.age}</div>
                <div class="gender-location">${getGenderDisplay(profile.gender)}</div>
            </div>
            <div class="personal-detail">${profile.location}</div>
            <div class="personal-detail">${profile.occupation}</div>
            <div class="ai-compatibility">AI Compatible</div>
        </div>
    `;
    
    return card;
}

function getGenderDisplay(gender) {
    const genderMap = {
        'M': 'Male',
        'F': 'Female',
        'T': 'Non-binary',
        'O': 'Other'
    };
    return genderMap[gender] || 'Other';
}

// Modal Functions
function showProfileModal(profile) {
    const modal = document.getElementById('profileModal');
    const modalName = document.getElementById('modalName');
    const modalImage = document.getElementById('modalImage');
    const modalDetails = document.getElementById('modalDetails');
    
    modalName.textContent = `${profile.name}, ${profile.age}`;
    modalImage.textContent = profile.avatar || '👤';
    
    modalDetails.innerHTML = `
        <p><strong>Location:</strong> ${profile.location}</p>
        <p><strong>Occupation:</strong> ${profile.occupation}</p>
        <p><strong>Bio:</strong> ${profile.bio}</p>
        <p><strong>AI Compatibility:</strong> ${profile.aiCompatibility}%</p>
    `;
    
    modal.style.display = 'block';
    modal.currentProfile = profile;
}

function closeModal() {
    document.getElementById('profileModal').style.display = 'none';
}

async function handleAction(action) {
    const modal = document.getElementById('profileModal');
    const profile = modal.currentProfile;
    
    if (!profile || !currentUser) return;
    
    try {
        await datingDB.addInteraction(currentUser.id, profile.id, action);
        
        if (action === 'like') {
            updateStatus(`You liked ${profile.name}! 💕`);
        } else {
            updateStatus(`Passed on ${profile.name}`);
        }
        
        closeModal();
        updateAIInsights();
        
    } catch (error) {
        console.error('Error handling action:', error);
        updateStatus('Error processing action: ' + error.message);
    }
}

async function updateAIInsights() {
    try {
        const insights = [];
        
        if (currentUser) {
            const interactions = await datingDB.getUserInteractions(currentUser.id);
            const likes = interactions.filter(i => i.type === 'like').length;
            const passes = interactions.filter(i => i.type === 'pass').length;
            
            insights.push(`You've liked ${likes} profiles and passed on ${passes}`);
            
            if (likes > passes) {
                insights.push('You seem optimistic about finding matches!');
            } else if (passes > likes) {
                insights.push('You have high standards - quality over quantity!');
            }
        }
        
        insights.push(`${currentProfiles.length} profiles available in current filter`);
        
        if (currentProfiles.length > 0) {
            const avgCompatibility = currentProfiles.reduce((sum, p) => sum + p.aiCompatibility, 0) / currentProfiles.length;
            insights.push(`Average AI compatibility: ${Math.round(avgCompatibility)}%`);
        }
        
        const insightsList = document.getElementById('aiInsightsList');
        insightsList.innerHTML = insights.map(insight => `<li>${insight}</li>`).join('');
        
    } catch (error) {
        console.error('Error updating AI insights:', error);
    }
}