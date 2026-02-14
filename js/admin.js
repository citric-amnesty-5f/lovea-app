// Admin Functions
async function initializeDB() {
    if (!currentUser?.isAdmin) return;
    
    try {
        await datingDB.clearAll();
        await datingDB.initializeDefaultData();
        updateStatus('Database reset successfully!');
        await loadProfiles();
    } catch (error) {
        updateStatus('Error resetting database: ' + error.message);
    }
}

async function showDBStats() {
    if (!currentUser?.isAdmin) return;
    
    try {
        const stats = await datingDB.getStats();
        const message = `Database Stats:
Users: ${stats.totalUsers} (${stats.adminUsers} admins)
Profiles: ${stats.totalProfiles}
Interactions: ${stats.totalInteractions}
Likes: ${stats.likes} | Passes: ${stats.passes}`;
        alert(message);
    } catch (error) {
        updateStatus('Error getting stats: ' + error.message);
    }
}

async function showUserStats() {
    if (!currentUser?.isAdmin) return;
    
    try {
        const users = await datingDB.getAllUsers();
        const userList = users.map(u => 
            `${u.name} (${u.email})${u.isAdmin ? ' [ADMIN]' : ''}`
        ).join('\n');
        
        alert(`All Users:\n\n${userList}`);
    } catch (error) {
        updateStatus('Error getting user stats: ' + error.message);
    }
}

async function addRandomProfile() {
    if (!currentUser?.isAdmin) return;
    
    const names = ['Chris', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Avery'];
    const locations = ['Manhattan, NY', 'Brooklyn, NY', 'Queens, NY', 'Bronx, NY'];
    const occupations = ['Teacher', 'Designer', 'Writer', 'Developer', 'Manager'];
    const avatars = ['👨‍💼', '👩‍🎨', '👨‍🏫', '👩‍💻', '👨‍🍳'];
    
    const profile = {
        name: names[Math.floor(Math.random() * names.length)],
        age: Math.floor(Math.random() * 20) + 22,
        gender: ['M', 'F', 'T'][Math.floor(Math.random() * 3)],
        location: locations[Math.floor(Math.random() * locations.length)],
        occupation: occupations[Math.floor(Math.random() * occupations.length)],
        bio: 'AI-generated profile for testing purposes.',
        aiCompatibility: Math.floor(Math.random() * 30) + 70,
        avatar: avatars[Math.floor(Math.random() * avatars.length)]
    };
    
    try {
        await datingDB.addProfile(profile);
        updateStatus(`Added profile: ${profile.name}`);
        await loadProfiles();
    } catch (error) {
        updateStatus('Error adding profile: ' + error.message);
    }
}