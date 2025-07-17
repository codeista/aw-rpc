// Analyze GREY army sprite spacing issue

const greyUnits = [
    { unit: 'INFANTRY', y: 1240 },
    { unit: 'MECH', y: 1335 },      // +95
    { unit: 'RECON', y: 1430 },     // +95
    { unit: 'TANK', y: 1449 },      // +19
    { unit: 'MEDIUMTANK', y: 1468 },// +19
    { unit: 'NEOTANK', y: 1487 },   // +19
    { unit: 'APC', y: 1506 },       // +19
    { unit: 'ANTIAIR', y: 1525 },   // +19
    { unit: 'ARTILLERY', y: 1544 }, // +19
    { unit: 'ROCKET', y: 1563 },    // +19
    { unit: 'MISSILE', y: 1582 },   // +19
    { unit: 'FIGHTER', y: 1601 }    // +19
];

console.log('GREY Army Y-coordinate Analysis:');
console.log('================================');

for (let i = 0; i < greyUnits.length; i++) {
    const gap = i > 0 ? greyUnits[i].y - greyUnits[i-1].y : 0;
    console.log(`${greyUnits[i].unit.padEnd(12)} Y=${greyUnits[i].y} ${gap > 0 ? `(+${gap})` : ''}`);
}

console.log('\nProblem: MECH and RECON have 95px gaps instead of 19px');
console.log('This suggests they might be on different sprite sheet rows');
console.log('\nTo fix GREY army alignment:');
console.log('1. MECH should be at Y=1259 (not 1335)');
console.log('2. RECON should be at Y=1278 (not 1430)');
console.log('3. All subsequent units need Y adjustment');