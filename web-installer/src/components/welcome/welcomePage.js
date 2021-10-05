import React from 'react';
import { Grid, Button } from '@material-ui/core';
import LoginContainer from 'containers/welcome/loginContainer';
import Background from 'assets/img/backgrounds/jake-wetton-4RiNCJiOrHM-unsplash.jpg';

function WelcomePage() {
  return (
    <div>
      <Grid container style={{ minHeight: '100vh' }}>
        <Grid
          item
          xs={12}
          sm={6}
          style={{
            backgroundImage: `url(${Background})`,
            backgroundSize: 'cover',
            backgroundRepeat: 'no-repeat',
          }}
        />
        <Grid
          container
          item
          xs={12}
          sm={6}
          alignItems="center"
          direction="column"
          justify="space-between"
          style={{ padding: 10 }}
        >
          <div />
          <div />
          <LoginContainer />
          <div />
          <Grid container justify="center" spacing={2}>
            <Grid item>
              <Button href="https://simply-vc.com.mt/" target="_blank">
                Visit the SimplyVC Website!
              </Button>
            </Grid>
            <Grid item>
              <Button href="https://twitter.com/Simply_VC" target="_blank">
                Follow us on Twitter!
              </Button>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </div>
  );
}

export default WelcomePage;
