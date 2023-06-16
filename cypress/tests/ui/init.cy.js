// Discovering Cypress

// Visiting url/website
describe('visit kedro-viz', () => {
  it('Visits the Kedro Viz Home Page', () => {
    cy.visit('/')
  })
});

// Testing commands
describe('testing main command', () => {
  it('checks the response of main api and stores in local storage', () => {
     cy.main()
  })
})

// Using Cypress Studio to generate tests
describe('test global toolbar', () => {
  /* ==== Test Created with Cypress Studio ==== */
  it('test generation with default locators', function() {
    /* ==== Generated with Cypress Studio ==== */
    cy.get('.pipeline-menu-button--logo > .pipeline-icon > path').click();
    cy.get('.active > .pipeline-icon--container > .pipeline-menu-button--large > .pipeline-icon').click();
    cy.get('[href="/experiment-tracking"] > .pipeline-icon--container > .pipeline-menu-button--large > .pipeline-icon').click();
    cy.get('[href="/"] > .pipeline-icon--container > .pipeline-menu-button--large > .pipeline-icon').click();
    cy.get('.pipeline-menu-button--theme > .pipeline-icon > path').click();
    cy.get('.pipeline-menu-button--settings > .pipeline-icon').click();
    cy.get('.run-details-modal-button-wrapper > :nth-child(1) > .button__btn').click();
    /* ==== End Cypress Studio ==== */
  });

  /* ==== Test Created with Cypress Studio ==== */
  it('test generation with recommended data selectors', function() {
    /* ==== Generated with Cypress Studio ==== */
    // Click Tests
    
    cy.get('[data-cy="Kedro Icon"]').click();
    cy.get('[data-cy="View your pipeline"]').click();
    cy.get('[data-cy="View your experiments"]').click();
    cy.get('[data-cy="Toggle Theme"]').click();
    cy.get('[data-cy="Toggle Theme"]').click();
    cy.get('[data-cy="Change the settings flags"]').click();
    cy.get('[role="dialog"]').should('be.visible').then(($dialog)=>{
      cy.wrap($dialog).find('[data-cy="Cancel Button in Settings Modal"]').click()
    });
    cy.get('[role="dialog"]').should('be.not.visible');

    // Hover/UnHover Tests

    // Hover View your pipeline
    cy.hover('[data-cy="View your pipeline"]');
    cy.get('[data-cy="View your pipeline"]').within(() => {
      return cy.get('span').should('have.class', 'pipeline-toolbar__label__visible')
    })
    // UnHover View your pipeline
    cy.unhover('[data-cy="View your pipeline"]');
    cy.get('[data-cy="View your pipeline"]').within(() => {
      return cy.get('span').should('not.have.class', 'pipeline-toolbar__label__visible')
    })

    // Hover View your experiments
    cy.hover('[data-cy="View your experiments"]');
    cy.get('[data-cy="View your experiments"]').within(() => {
      return cy.get('span').should('have.class', 'pipeline-toolbar__label__visible')
    })
    // UnHover View your experiments
    cy.unhover('[data-cy="View your experiments"]');
    cy.get('[data-cy="View your experiments"]').within(() => {
      return cy.get('span').should('not.have.class', 'pipeline-toolbar__label__visible')
    })

    // Hover Toggle Theme
    cy.hover('[data-cy="Toggle Theme"]');
    cy.get('[data-cy="Toggle Theme"]').within(() => {
      return cy.get('span').should('have.class', 'pipeline-toolbar__label__visible')
    })
    // UnHover Toggle Theme
    cy.unhover('[data-cy="Toggle Theme"]');
    cy.get('[data-cy="Toggle Theme"]').within(() => {
      return cy.get('span').should('not.have.class', 'pipeline-toolbar__label__visible')
    })

    // Hover Change the settings flags
    cy.hover('[data-cy="Change the settings flags"]');
    cy.get('[data-cy="Change the settings flags"]').within(() => {
      return cy.get('span').should('have.class', 'pipeline-toolbar__label__visible')
    })
    // UnHover Change the settings flags
    cy.unhover('[data-cy="Change the settings flags"]');
    cy.get('[data-cy="Change the settings flags"]').within(() => {
      return cy.get('span').should('not.have.class', 'pipeline-toolbar__label__visible')
    })
    /* ==== End Cypress Studio ==== */
  });
})



