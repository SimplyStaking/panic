import React from 'react';
// nodejs library that concatenates classes
import classNames from 'classnames';
// nodejs library to set properties for components
import PropTypes from 'prop-types';

// core components
import useStyles from 'assets/jss/material-kit-react/components/parallaxStyle';

export default function Parallax(props) {
  let windowScrollTop;
  if (window.innerWidth >= 768) {
    windowScrollTop = window.pageYOffset / 3;
  } else {
    windowScrollTop = 0;
  }
  const [transform, setTransform] = React.useState(
    `translate3d(0,${windowScrollTop}px,0)`,
  );
  const resetTransform = () => {
    windowScrollTop = window.pageYOffset / 3;
    setTransform(`translate3d(0,${windowScrollTop}px,0)`);
  };
  React.useEffect(() => {
    if (window.innerWidth >= 768) {
      window.addEventListener('scroll', resetTransform);
    }
    return function cleanup() {
      if (window.innerWidth >= 768) {
        window.removeEventListener('scroll', resetTransform);
      }
    };
  });
  const {
    filter, className, children, style, image, small,
  } = props;
  const classes = useStyles();
  const parallaxClasses = classNames({
    [classes.parallax]: true,
    [classes.filter]: filter,
    [classes.small]: small,
    [className]: className !== undefined,
  });
  return (
    <div
      className={parallaxClasses}
      style={{
        ...style,
        backgroundImage: `url(${image})`,
        backgroundSize: 'cover',
        minHeight: '1rem',
        transform,
      }}
    >
      {children}
    </div>
  );
}

Parallax.propTypes = {
  className: PropTypes.string.isRequired,
  filter: PropTypes.bool.isRequired,
  children: PropTypes.node.isRequired,
  style: PropTypes.string.isRequired,
  image: PropTypes.string.isRequired,
  small: PropTypes.bool.isRequired,
};
