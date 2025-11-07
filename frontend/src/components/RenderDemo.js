import React, {useState} from 'react';

function RenderDemo(){
    const [count, setCount] = useState(0);
    const [text, setText] = useState("React는 렌더링의 마법사 !!");

    console.log('✅ RenderDemo 렌더링 발생! (Virtual DOM 비교 후 실제 DOM 업데이트)');

    return (
        <div style={{padding: 20}}>
            <h2>{text}</h2>
            <p>현재 카운트: {count}</p>

            <button onClick={() => setCount(count + 1)}>+1 증가</button>
            <button onClick={()=> setText('상태가 변경되면 다시 렌더링됩니다!')}></button>

            <p style={{ marginTop: 20, color: 'gray' }}>
                (콘솔을 열어보세요! <br />렌더링이 일어날 때마다 로그가 찍힙니다.)
            </p>
        </div>
    );
}

export default RenderDemo;