import React from 'react';
// nodejs library to set properties for components
import PropTypes from 'prop-types';
// nodejs library that concatenates classes
import classNames from 'classnames';

import useStyles from 'assets/jss/material-kit-react/components/infoStyle';

export default function InfoArea(props) {
  const classes = useStyles();
  const {
    title, description, iconColor, vertical,
  } = props;
  const iconWrapper = classNames({
    [classes.iconWrapper]: true,
    [classes[iconColor]]: true,
    [classes.iconWrapperVertical]: vertical,
  });
  const iconClasses = classNames({
    [classes.icon]: true,
    [classes.iconVertical]: vertical,
  });
  return (
    <div className={classes.infoArea}>
      <div className={iconWrapper}>
        <props.icon className={iconClasses} />
      </div>
      <div className={classes.descriptionWrapper}>
        <h4 className={classes.title}>{title}</h4>
        <div className={classes.description}>{description}</div>
      </div>
    </div>
  );
}

InfoArea.defaultProps = {
  iconColor: 'gray',
};

InfoArea.propTypes = {
  title: PropTypes.string.isRequired,
  // eslint-disable-next-line react/forbid-prop-types
  description: PropTypes.object.isRequired,
  iconColor: PropTypes.oneOf([
    'primary',
    'warning',
    'danger',
    'success',
    'info',
    'rose',
    'gray',
    '#000000',
  ]),
  vertical: PropTypes.bool.isRequired,
};
