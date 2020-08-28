import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import { Grid, Box, Accordion } from '@material-ui/core';
import AccordionSummary from '@material-ui/core/AccordionSummary';
import AccordionDetails from '@material-ui/core/AccordionDetails';
import Typography from '@material-ui/core/Typography';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';

import TelegramIcon from '../../assets/icons/telegram.svg';

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
  },
  paper: {
    padding: theme.spacing(2),
    textAlign: 'center',
    color: theme.palette.text.primary,
  },
  icon: {
    paddingRight: '1rem',
  },
  heading: {
    fontSize: theme.typography.pxToRem(15),
    fontWeight: theme.typography.fontWeightRegular,
  },
}));

function ChannelsGrid() {
  const classes = useStyles();

  return (
    <Box p={2} className={classes.root}>
      <Box
        p={3}
        border={1}
        borderRadius="borderRadius"
        borderColor="grey.300"
      >
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                aria-controls="panel1a-content"
                id="panel1a-header"
              >
                <img
                  src={TelegramIcon}
                  className={classes.icon}
                  alt="TelegramIcon"
                />
                <Typography
                  style={{ textAlign: 'center' }}
                  variant="h5"
                  align="center"
                  gutterBottom
                >
                  Telegram
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <h1>Chicken</h1>
              </AccordionDetails>
            </Accordion>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
}

export default ChannelsGrid;
