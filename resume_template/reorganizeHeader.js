// reorganizeHeader.js
function reorganizeHeader() {
  const h1 = document.querySelector('h1');
  if (!h1) return; 
  let currentNode = h1;
  const headerInfoElements = [];
  const contactInfoElements = [];
  let firstAnchorFound = false;
  while (currentNode && currentNode.tagName !== 'H2') {
    if (currentNode.tagName === 'A') {
      if (!firstAnchorFound) {
        headerInfoElements.push(currentNode);
        firstAnchorFound = true;
      } else {
        contactInfoElements.push(currentNode);
      }
    } else {
      headerInfoElements.push(currentNode);
    }
    currentNode = currentNode.nextElementSibling;
  }
  const newHeader = document.createElement('header');
  const headerInfoDiv = document.createElement('div');
  headerInfoDiv.className = 'header-info';
  headerInfoElements.forEach(el => {
    headerInfoDiv.appendChild(el);
  });
  const contactInfoDiv = document.createElement('div');
  contactInfoDiv.className = 'contact-info';
  contactInfoElements.forEach(el => {
    contactInfoDiv.appendChild(el);
  });
  newHeader.appendChild(headerInfoDiv);
  newHeader.appendChild(contactInfoDiv);
  const h2 = document.querySelector('h2');
  if (h2) {
    h2.parentNode.insertBefore(newHeader, h2);
  }
}

  setTimeout(function() {
    reorganizeHeader();
  }, 100); 
