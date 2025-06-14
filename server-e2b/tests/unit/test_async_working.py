"""
Simple test to verify async tests are working correctly
"""
import pytest
import asyncio

@pytest.mark.anyio
async def test_simple_async():
    """Test that async tests run properly"""
    await asyncio.sleep(0.01)
    assert True

@pytest.mark.anyio 
async def test_async_with_return_value():
    """Test async function with return value"""
    async def get_value():
        await asyncio.sleep(0.01)
        return 42
    
    result = await get_value()
    assert result == 42

@pytest.mark.anyio
async def test_multiple_awaits():
    """Test multiple async operations"""
    results = []
    for i in range(3):
        await asyncio.sleep(0.01)
        results.append(i)
    
    assert results == [0, 1, 2]