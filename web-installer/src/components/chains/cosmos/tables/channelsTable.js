import React from 'react';
import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import {
  Grid, FormControlLabel, Checkbox, List, ListItem, Typography,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

const ChannelsTable = (props) => {
  const classes = useStyles();

  const {
    config,
    handleChange,
    telegrams,
    opsgenies,
    emails,
    pagerduties,
    twilios,
    saveTelegramDetails,
    removeTelegramDetails,
  } = props;

  return (
    <Grid container className={classes.root} spacing={2}>
      <Grid item xs={12}>
        <Grid container justify="center" spacing={3}>
          <Grid item>
            <Paper className={classes.paper}>
              <Typography>
                Telegram
              </Typography>
              <div style={{ maxHeight: 300, minHeight: 300, overflow: 'auto' }}>
                <List>
                  {telegrams.map((telegram) => (
                    <ListItem key={telegram.botName}>
                      <FormControlLabel
                        control={(
                          <Checkbox
                            checked={config.telegrams.includes(telegram.botName)}
                            onClick={() => {
                              if (config.telegrams.includes(telegram.botName)) {
                                removeTelegramDetails(telegram.botName);
                              } else {
                                saveTelegramDetails(telegram.botName);
                              }
                            }}
                            onChange={handleChange}
                            name="telegrams"
                            color="primary"
                          />
                        )}
                        label={telegram.botName}
                        labelPlacement="start"
                      />
                    </ListItem>
                  ))}
                </List>
              </div>
            </Paper>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
};

ChannelsTable.propTypes = {
  telegrams: PropTypes.arrayOf(PropTypes.shape({
    botName: PropTypes.string.isRequired,
  })).isRequired,
  config: PropTypes.shape({
    telegrams: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
  }).isRequired,
  handleChange: PropTypes.func.isRequired,
  saveTelegramDetails: PropTypes.func.isRequired,
  removeTelegramDetails: PropTypes.func.isRequired,
};

export default ChannelsTable;
