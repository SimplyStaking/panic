import React from 'react';
import PropTypes from 'prop-types';
import{ forbidExtraProps }from 'airbnb-prop-types';
import { Accordion, Grid } from '@material-ui/core';
import AccordionSummary from '@material-ui/core/AccordionSummary';
import AccordionDetails from '@material-ui/core/AccordionDetails';
import Typography from '@material-ui/core/Typography';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';

function FormAccordion({
  icon, name, form, table,
}) {
  return (
    <Accordion>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="panel1a-content"
        id="panel1a-header"
      >
        <img src={icon} className="icon" alt="TelegramIcon" />
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
        <Grid container spacing={3}>
          <Grid item xs={12}>
            {form}
          </Grid>
          <Grid item xs={12}>
            {table}
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
}

FormAccordion.propTypes = forbidExtraProps({
  icon: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  form: PropTypes.element.isRequired,
  table: PropTypes.element.isRequired,
});

export default FormAccordion;
