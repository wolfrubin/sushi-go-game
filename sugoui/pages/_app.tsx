import React from 'react';
import type { AppProps } from 'next/app'

import '../styles/darkly.bootstrap.min.css';



function SushiGoApp( {Component, pageProps}: AppProps) {
    return <Component {...pageProps} />
}

export default SushiGoApp