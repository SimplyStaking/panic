import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { Accordion, Grid } from '@material-ui/core';
import AccordionSummary from '@material-ui/core/AccordionSummary';
import AccordionDetails from '@material-ui/core/AccordionDetails';
import Typography from '@material-ui/core/Typography';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';

/*
 * Accordion, drop down that contains the chain icon, name, table containing
 * all the setup chains which can be loaded.
*/
function ChainAccordion({icon, name, button, table}) {
  return (
    <div className="flex_root">
      <Accordion>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="panel1a-content"
          id="panel1a-header"
        >
          <img
            src={icon}
            className="icon"
            alt="Chain Icon"
          />
          <Typography
            style={{ textAlign: 'center' }}
            variant="h5"
            align="center"
            gutterBottom
          >
            {name}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container>
            <Grid item xs={12} />
            <br />
            <br />
            <Grid item xs={5} />
            <Grid item xs={2}>
              {button}
            </Grid>
            <Grid item xs={5} />
            <Grid item xs={12} />
            <br />
            <br />
            <Grid item xs={12}>
              {table}
            </Grid>
            <br />
            <br />
            <Grid item xs={12} />
          </Grid>
        </AccordionDetails>
      </Accordion>
    </div>
  );
}

ChainAccordion.propTypes = forbidExtraProps({
  icon: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  button: PropTypes.element.isRequired,
  table: PropTypes.element.isRequired,
});

export default ChainAccordion;
